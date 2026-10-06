/*
 * sys_power_hook.c
 * PowerController Pure Custom Native Session & Hardware Power Monitor (순수 창작 세션 훅 및 전원 감시 엔진)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Real-time Windows session change notification hook (WTSRegisterSessionNotification)
 *  - Instant detection of screen lock (Win + L), unlock, and session state changes
 *  - Hardware Battery & UPS status query (GetSystemPowerStatus) with zero CPU overhead
 *  - Ultra-fast native OS power actions (LockWorkStation, Monitor Sleep) without PowerShell or rundll32
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

#define POWERHOOK_API __declspec(dllexport)

#ifndef WM_WTSSESSION_CHANGE
#define WM_WTSSESSION_CHANGE 0x02B1
#endif

#ifndef WTS_CONSOLE_CONNECT
#define WTS_CONSOLE_CONNECT        0x1
#define WTS_CONSOLE_DISCONNECT     0x2
#define WTS_REMOTE_CONNECT         0x3
#define WTS_REMOTE_DISCONNECT      0x4
#define WTS_SESSION_LOGON          0x5
#define WTS_SESSION_LOGOFF         0x6
#define WTS_SESSION_LOCK           0x7
#define WTS_SESSION_UNLOCK         0x8
#define WTS_SESSION_REMOTE_CONTROL 0x9
#endif

#ifndef NOTIFY_FOR_THIS_SESSION
#define NOTIFY_FOR_THIS_SESSION 0
#endif

typedef BOOL (WINAPI *pfnWTSRegisterSessionNotification)(HWND, DWORD);
typedef BOOL (WINAPI *pfnWTSUnRegisterSessionNotification)(HWND);

static pfnWTSRegisterSessionNotification g_pfnWTSRegister = NULL;
static pfnWTSUnRegisterSessionNotification g_pfnWTSUnRegister = NULL;
static HMODULE g_hWtsLib = NULL;

/* Session Event FIFO Queue */
#define SESSION_EVENT_QUEUE_SIZE 64
typedef struct {
    int event_type;
    int session_id;
} SessionEvent;

static SessionEvent g_EventQueue[SESSION_EVENT_QUEUE_SIZE];
static int g_QueueHead = 0;
static int g_QueueTail = 0;
static int g_QueueCount = 0;
static CRITICAL_SECTION g_csSession;
static BOOL g_csInitialized = FALSE;

/* Session state */
static volatile int g_LastSessionEvent = 0;
static volatile BOOL g_IsSessionLocked = FALSE;

/* Worker thread & message window state */
static HANDLE g_hWorkerThread = NULL;
static DWORD g_WorkerThreadId = 0;
static HWND g_hMsgWnd = NULL;
static volatile BOOL g_HookRunning = FALSE;
static HANDLE g_hInitEvent = NULL;

static void EnsureCSInitialized(void) {
    if (!g_csInitialized) {
        InitializeCriticalSection(&g_csSession);
        g_csInitialized = TRUE;
    }
}

static void InitWtsFunctions(void) {
    if (g_hWtsLib == NULL) {
        g_hWtsLib = LoadLibraryA("wtsapi32.dll");
        if (g_hWtsLib != NULL) {
            g_pfnWTSRegister = (pfnWTSRegisterSessionNotification)GetProcAddress(g_hWtsLib, "WTSRegisterSessionNotification");
            g_pfnWTSUnRegister = (pfnWTSUnRegisterSessionNotification)GetProcAddress(g_hWtsLib, "WTSUnRegisterSessionNotification");
        }
    }
}

static LRESULT CALLBACK SessionHookWndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_WTSSESSION_CHANGE) {
        int evType = (int)wParam;
        int sessId = (int)lParam;

        g_LastSessionEvent = evType;
        if (evType == WTS_SESSION_LOCK) {
            g_IsSessionLocked = TRUE;
        } else if (evType == WTS_SESSION_UNLOCK) {
            g_IsSessionLocked = FALSE;
        }

        EnsureCSInitialized();
        EnterCriticalSection(&g_csSession);
        if (g_QueueCount < SESSION_EVENT_QUEUE_SIZE) {
            g_EventQueue[g_QueueTail].event_type = evType;
            g_EventQueue[g_QueueTail].session_id = sessId;
            g_QueueTail = (g_QueueTail + 1) % SESSION_EVENT_QUEUE_SIZE;
            g_QueueCount++;
        }
        LeaveCriticalSection(&g_csSession);
        return 0;
    }
    return DefWindowProc(hWnd, msg, wParam, lParam);
}

static DWORD WINAPI SessionHookThreadWorker(LPVOID lpParam) {
    InitWtsFunctions();

    HINSTANCE hInstance = GetModuleHandle(NULL);
    const char* className = "PowerController_SessionHookClass";

    WNDCLASSEXA wc;
    memset(&wc, 0, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = SessionHookWndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = className;

    RegisterClassExA(&wc);

    HWND hWnd = CreateWindowExA(
        0,
        className,
        "PowerSessionHookWindow",
        0, 0, 0, 0, 0,
        HWND_MESSAGE,
        NULL,
        hInstance,
        NULL
    );

    if (hWnd == NULL) {
        g_HookRunning = FALSE;
        if (g_hInitEvent) SetEvent(g_hInitEvent);
        return 1;
    }

    g_hMsgWnd = hWnd;

    if (g_pfnWTSRegister) {
        g_pfnWTSRegister(hWnd, NOTIFY_FOR_THIS_SESSION);
    }

    g_HookRunning = TRUE;
    if (g_hInitEvent) {
        SetEvent(g_hInitEvent);
    }

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    if (g_pfnWTSUnRegister && g_hMsgWnd) {
        g_pfnWTSUnRegister(g_hMsgWnd);
    }

    if (g_hMsgWnd) {
        DestroyWindow(g_hMsgWnd);
        g_hMsgWnd = NULL;
    }

    UnregisterClassA(className, hInstance);
    g_HookRunning = FALSE;
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsureCSInitialized();
            break;
        case DLL_PROCESS_DETACH:
            if (g_HookRunning) {
                if (g_WorkerThreadId != 0) {
                    PostThreadMessage(g_WorkerThreadId, WM_QUIT, 0, 0);
                }
                if (g_hWorkerThread != NULL) {
                    WaitForSingleObject(g_hWorkerThread, 1000);
                    CloseHandle(g_hWorkerThread);
                    g_hWorkerThread = NULL;
                }
            }
            if (g_csInitialized) {
                DeleteCriticalSection(&g_csSession);
                g_csInitialized = FALSE;
            }
            if (g_hWtsLib != NULL) {
                FreeLibrary(g_hWtsLib);
                g_hWtsLib = NULL;
            }
            break;
    }
    return TRUE;
}

/* --------------------------------------------------------------------------
 * Exported C ABI Functions
 * -------------------------------------------------------------------------- */

/*
 * Start background session change notification hook
 */
POWERHOOK_API BOOL NativeStartSessionHook(void) {
    EnsureCSInitialized();

    if (g_HookRunning) {
        return TRUE;
    }

    /* Reset event queue */
    EnterCriticalSection(&g_csSession);
    g_QueueHead = 0;
    g_QueueTail = 0;
    g_QueueCount = 0;
    LeaveCriticalSection(&g_csSession);

    g_hInitEvent = CreateEvent(NULL, FALSE, FALSE, NULL);

    g_hWorkerThread = CreateThread(
        NULL,
        0,
        SessionHookThreadWorker,
        NULL,
        0,
        &g_WorkerThreadId
    );

    if (g_hWorkerThread == NULL) {
        if (g_hInitEvent) {
            CloseHandle(g_hInitEvent);
            g_hInitEvent = NULL;
        }
        return FALSE;
    }

    /* Wait up to 1.5s for worker window initialization */
    if (g_hInitEvent) {
        WaitForSingleObject(g_hInitEvent, 1500);
        CloseHandle(g_hInitEvent);
        g_hInitEvent = NULL;
    }

    return g_HookRunning;
}

/*
 * Stop background session change notification hook
 */
POWERHOOK_API BOOL NativeStopSessionHook(void) {
    if (!g_HookRunning) {
        return TRUE;
    }

    if (g_WorkerThreadId != 0) {
        PostThreadMessage(g_WorkerThreadId, WM_QUIT, 0, 0);
    }

    if (g_hWorkerThread != NULL) {
        WaitForSingleObject(g_hWorkerThread, 1200);
        CloseHandle(g_hWorkerThread);
        g_hWorkerThread = NULL;
    }

    g_WorkerThreadId = 0;
    g_HookRunning = FALSE;
    return TRUE;
}

/*
 * Returns last session event code (e.g. 7 for lock, 8 for unlock)
 */
POWERHOOK_API int NativeGetLastSessionEvent(void) {
    return g_LastSessionEvent;
}

/*
 * Dequeues next session event from in-memory FIFO queue.
 * Returns 1 if event dequeued, 0 if queue empty.
 */
POWERHOOK_API int NativeGetNextSessionEvent(int* out_event_type, int* out_session_id) {
    if (!out_event_type || !out_session_id) {
        return 0;
    }

    EnsureCSInitialized();
    EnterCriticalSection(&g_csSession);

    if (g_QueueCount <= 0) {
        LeaveCriticalSection(&g_csSession);
        return 0;
    }

    *out_event_type = g_EventQueue[g_QueueHead].event_type;
    *out_session_id = g_EventQueue[g_QueueHead].session_id;

    g_QueueHead = (g_QueueHead + 1) % SESSION_EVENT_QUEUE_SIZE;
    g_QueueCount--;

    LeaveCriticalSection(&g_csSession);
    return 1;
}

/*
 * Returns TRUE if current session is locked (Win + L)
 */
POWERHOOK_API BOOL NativeIsSessionLocked(void) {
    return g_IsSessionLocked;
}

/*
 * Hardware Battery and UPS monitoring via GetSystemPowerStatus
 */
POWERHOOK_API BOOL NativeGetBatteryStatus(int* out_ac_status, int* out_battery_flag, int* out_percent, int* out_life_time) {
    SYSTEM_POWER_STATUS sps;
    if (!GetSystemPowerStatus(&sps)) {
        return FALSE;
    }

    if (out_ac_status) *out_ac_status = (int)sps.ACLineStatus;
    if (out_battery_flag) *out_battery_flag = (int)sps.BatteryFlag;
    if (out_percent) *out_percent = (int)sps.BatteryLifePercent;
    if (out_life_time) *out_life_time = (int)sps.BatteryLifeTime;

    return TRUE;
}

/*
 * Returns TRUE if PC is running on battery power (AC offline)
 */
POWERHOOK_API BOOL NativeIsOnBatteryPower(void) {
    SYSTEM_POWER_STATUS sps;
    if (GetSystemPowerStatus(&sps)) {
        return (sps.ACLineStatus == 0); /* 0 = Offline (Battery) */
    }
    return FALSE;
}

/*
 * Returns battery percent (0..100) or -1 if no battery / unknown
 */
POWERHOOK_API int NativeGetBatteryPercent(void) {
    SYSTEM_POWER_STATUS sps;
    if (GetSystemPowerStatus(&sps)) {
        if (sps.BatteryLifePercent != 255) {
            return (int)sps.BatteryLifePercent;
        }
    }
    return -1;
}

/*
 * Returns TRUE if battery is at or below threshold percent
 */
POWERHOOK_API BOOL NativeIsBatteryCritical(int threshold_percent) {
    SYSTEM_POWER_STATUS sps;
    if (GetSystemPowerStatus(&sps)) {
        if (sps.ACLineStatus == 0 && sps.BatteryLifePercent != 255) {
            return ((int)sps.BatteryLifePercent <= threshold_percent);
        }
    }
    return FALSE;
}

/*
 * Sub-millisecond Native Lock WorkStation (replaces rundll32)
 */
POWERHOOK_API BOOL NativeLockWorkStation(void) {
    return LockWorkStation();
}

/*
 * Sub-millisecond Native Turn Off Monitor (replaces PowerShell inline compile)
 */
POWERHOOK_API BOOL NativeTurnOffMonitor(void) {
    SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2);
    return TRUE;
}
