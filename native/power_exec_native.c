/*
 * power_exec_native.c
 * PowerController Pure Custom Native OS Power Execution & Privilege Engine
 * (순수 창작 Win32 전원 권한 상승 및 OS 전원 실행 엔진)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Acquires SE_SHUTDOWN_NAME privilege directly on process token via Advapi32
 *  - Executes Shutdown, Reboot, Logoff via InitiateSystemShutdownExW / ExitWindowsEx
 *  - Executes Sleep (S3) and Hibernate (S4) via official C ABI SetSuspendState (powrprof)
 *    instead of broken rundll32.exe signature mismatch or cmd/shutdown subprocesses
 *  - Queries real ACPI hardware suspend/hibernate capabilities
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

#define POWEREXEC_API __declspec(dllexport)

#ifndef SHTDN_REASON_MAJOR_APPLICATION
#define SHTDN_REASON_MAJOR_APPLICATION 0x00040000
#endif
#ifndef SHTDN_REASON_MINOR_MAINTENANCE
#define SHTDN_REASON_MINOR_MAINTENANCE 0x00000001
#endif
#ifndef SHTDN_REASON_FLAG_PLANNED
#define SHTDN_REASON_FLAG_PLANNED 0x80000000
#endif
#ifndef EWX_FORCEIFHUNG
#define EWX_FORCEIFHUNG 0x00000010
#endif

typedef BOOLEAN (WINAPI *pfnSetSuspendState)(BOOLEAN Hibernate, BOOLEAN ForceCritical, BOOLEAN DisableWakeEvent);
typedef BOOLEAN (WINAPI *pfnIsPwrSuspendAllowed)(void);
typedef BOOLEAN (WINAPI *pfnIsPwrHibernateAllowed)(void);

static CRITICAL_SECTION g_csPowr;
static BOOL g_csPowrInit = FALSE;
static HMODULE g_hPowrProf = NULL;
static pfnSetSuspendState g_pfnSetSuspendState = NULL;
static pfnIsPwrSuspendAllowed g_pfnIsPwrSuspendAllowed = NULL;
static pfnIsPwrHibernateAllowed g_pfnIsPwrHibernateAllowed = NULL;

static void EnsurePowrCS(void) {
    if (!g_csPowrInit) {
        InitializeCriticalSection(&g_csPowr);
        g_csPowrInit = TRUE;
    }
}

static BOOL EnsurePowrProfLoaded(void) {
    EnsurePowrCS();
    EnterCriticalSection(&g_csPowr);
    if (g_hPowrProf == NULL) {
        g_hPowrProf = LoadLibraryA("powrprof.dll");
        if (g_hPowrProf != NULL) {
            g_pfnSetSuspendState = (pfnSetSuspendState)GetProcAddress(g_hPowrProf, "SetSuspendState");
            g_pfnIsPwrSuspendAllowed = (pfnIsPwrSuspendAllowed)GetProcAddress(g_hPowrProf, "IsPwrSuspendAllowed");
            g_pfnIsPwrHibernateAllowed = (pfnIsPwrHibernateAllowed)GetProcAddress(g_hPowrProf, "IsPwrHibernateAllowed");
        }
    }
    BOOL ok = (g_hPowrProf != NULL && g_pfnSetSuspendState != NULL);
    LeaveCriticalSection(&g_csPowr);
    return ok;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsurePowrCS();
            break;
        case DLL_PROCESS_DETACH:
            if (lpvReserved == NULL) {
                if (g_hPowrProf != NULL) {
                    FreeLibrary(g_hPowrProf);
                    g_hPowrProf = NULL;
                }
                if (g_csPowrInit) {
                    DeleteCriticalSection(&g_csPowr);
                    g_csPowrInit = FALSE;
                }
            }
            break;
    }
    return TRUE;
}

/* --------------------------------------------------------------------------
 * Exported C ABI Functions
 * -------------------------------------------------------------------------- */

/*
 * Enables SE_SHUTDOWN_NAME privilege on the current process token.
 * Must succeed before InitiateSystemShutdownExW / ExitWindowsEx / SetSuspendState.
 */
POWEREXEC_API BOOL NativeEnableShutdownPrivilege(void) {
    HANDLE hToken = NULL;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) {
        return FALSE;
    }

    TOKEN_PRIVILEGES tkp;
    ZeroMemory(&tkp, sizeof(tkp));

    if (!LookupPrivilegeValueW(NULL, SE_SHUTDOWN_NAME, &tkp.Privileges[0].Luid)) {
        CloseHandle(hToken);
        return FALSE;
    }

    tkp.PrivilegeCount = 1;
    tkp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;

    SetLastError(ERROR_SUCCESS);
    BOOL adjOk = AdjustTokenPrivileges(hToken, FALSE, &tkp, 0, NULL, NULL);
    DWORD err = GetLastError();
    CloseHandle(hToken);

    /* AdjustTokenPrivileges can return TRUE even when err == ERROR_NOT_ALL_ASSIGNED */
    return (adjOk && err == ERROR_SUCCESS);
}

/*
 * Queries ACPI power state capabilities and shutdown privilege status.
 */
POWEREXEC_API BOOL NativeCheckPowerCapabilities(int* out_can_suspend, int* out_can_hibernate, int* out_has_shutdown_priv) {
    EnsurePowrProfLoaded();

    if (out_can_suspend) {
        *out_can_suspend = (g_pfnIsPwrSuspendAllowed && g_pfnIsPwrSuspendAllowed()) ? 1 : 0;
    }
    if (out_can_hibernate) {
        *out_can_hibernate = (g_pfnIsPwrHibernateAllowed && g_pfnIsPwrHibernateAllowed()) ? 1 : 0;
    }
    if (out_has_shutdown_priv) {
        *out_has_shutdown_priv = NativeEnableShutdownPrivilege() ? 1 : 0;
    }
    return TRUE;
}

/*
 * Executes system shutdown or reboot directly via Win32 API (no shutdown.exe spawn).
 */
POWEREXEC_API BOOL NativeExecuteSystemShutdown(BOOL reboot, BOOL force, DWORD timeout_sec, const wchar_t* reason) {
    NativeEnableShutdownPrivilege();

    const wchar_t* msg = (reason && reason[0] != L'\0')
        ? reason
        : L"PowerController Scheduled Power Execution";

    DWORD reasonCode = SHTDN_REASON_MAJOR_APPLICATION | SHTDN_REASON_MINOR_MAINTENANCE | SHTDN_REASON_FLAG_PLANNED;

    /* For timed shutdowns (>0s) or standard power-off, InitiateSystemShutdownExW is atomic and clean */
    if (InitiateSystemShutdownExW(
            NULL,
            (LPWSTR)msg,
            timeout_sec,
            force ? TRUE : FALSE,
            reboot ? TRUE : FALSE,
            reasonCode)) {
        return TRUE;
    }

    /* Fallback to ExitWindowsEx if InitiateSystemShutdownExW is blocked in current session */
    UINT flags = reboot ? EWX_REBOOT : (EWX_SHUTDOWN | EWX_POWEROFF);
    flags |= force ? EWX_FORCE : EWX_FORCEIFHUNG;

    if (ExitWindowsEx(flags, reasonCode)) {
        return TRUE;
    }

    return FALSE;
}

/*
 * Executes Sleep (hibernate=FALSE) or Hibernate (hibernate=TRUE) using official C ABI SetSuspendState.
 * Avoids the rundll32.exe powrprof.dll,SetSuspendState ABI signature corruption bug.
 */
POWEREXEC_API BOOL NativeExecuteSuspendState(BOOL hibernate, BOOL force_critical) {
    if (!EnsurePowrProfLoaded()) {
        return FALSE;
    }

    if (hibernate) {
        if (g_pfnIsPwrHibernateAllowed && !g_pfnIsPwrHibernateAllowed()) {
            return FALSE;
        }
    } else {
        if (g_pfnIsPwrSuspendAllowed && !g_pfnIsPwrSuspendAllowed()) {
            return FALSE;
        }
    }

    NativeEnableShutdownPrivilege();

    return g_pfnSetSuspendState(
        hibernate ? TRUE : FALSE,
        force_critical ? TRUE : FALSE,
        FALSE /* DisableWakeEvent = FALSE so RTC wake timers remain active */
    ) ? TRUE : FALSE;
}

/*
 * Executes immediate interactive session logoff via ExitWindowsEx (no shutdown /l subprocess).
 */
POWEREXEC_API BOOL NativeExecuteLogoff(BOOL force) {
    UINT flags = EWX_LOGOFF | (force ? EWX_FORCE : EWX_FORCEIFHUNG);
    DWORD reasonCode = SHTDN_REASON_MAJOR_APPLICATION | SHTDN_REASON_MINOR_MAINTENANCE;
    return ExitWindowsEx(flags, reasonCode) ? TRUE : FALSE;
}

/*
 * Aborts any pending InitiateSystemShutdownExW countdown.
 */
POWEREXEC_API BOOL NativeAbortSystemShutdown(void) {
    NativeEnableShutdownPrivilege();
    return AbortSystemShutdownW(NULL) ? TRUE : FALSE;
}
