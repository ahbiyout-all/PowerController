/*
 * PowerCoreNative.c
 * PowerController Pure Custom Native Engine (순수 창작 네이티브 코어 엔진)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - High-precision Hardware RTC Wake-up Timer (SetWaitableTimer with fResume=TRUE)
 *  - Native Thread Execution State Management (Sleep & Display prevention)
 *  - 100% Silent Process Tree Killer (Toolhelp32 + TerminateProcess without spawning taskkill)
 *  - Fast Process Termination by image name
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <wchar.h>
#include <stdlib.h>

#define POWER_CORE_API __declspec(dllexport)

static HANDLE g_hWakeTimer = NULL;
static CRITICAL_SECTION g_csTimer;
static BOOL g_csInitialized = FALSE;

static void EnsureCriticalSectionInitialized(void) {
    if (!g_csInitialized) {
        InitializeCriticalSection(&g_csTimer);
        g_csInitialized = TRUE;
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsureCriticalSectionInitialized();
            break;
        case DLL_PROCESS_DETACH:
            if (lpvReserved == NULL && g_csInitialized) {
                EnterCriticalSection(&g_csTimer);
                if (g_hWakeTimer != NULL) {
                    CancelWaitableTimer(g_hWakeTimer);
                    CloseHandle(g_hWakeTimer);
                    g_hWakeTimer = NULL;
                }
                LeaveCriticalSection(&g_csTimer);
                DeleteCriticalSection(&g_csTimer);
                g_csInitialized = FALSE;
            }
            break;
    }
    return TRUE;
}

/* --------------------------------------------------------------------------
 * 1. Hardware Wake-up Timer (하드웨어 웨이크업 타이머)
 * -------------------------------------------------------------------------- */

POWER_CORE_API BOOL NativeIsHardwareWakeSupported(void) {
    HANDLE hTimer = CreateWaitableTimerW(NULL, TRUE, NULL);
    if (!hTimer) {
        return FALSE;
    }
    CloseHandle(hTimer);
    return TRUE;
}

POWER_CORE_API BOOL NativeSetHardwareWakeTimer(double seconds) {
    if (seconds <= 0.0) {
        return FALSE;
    }

    EnsureCriticalSectionInitialized();
    EnterCriticalSection(&g_csTimer);

    if (g_hWakeTimer != NULL) {
        CancelWaitableTimer(g_hWakeTimer);
        CloseHandle(g_hWakeTimer);
        g_hWakeTimer = NULL;
    }

    /* Create manual-reset waitable timer */
    g_hWakeTimer = CreateWaitableTimerW(NULL, TRUE, L"PowerController_HardwareWakeTimer");
    if (g_hWakeTimer == NULL) {
        g_hWakeTimer = CreateWaitableTimerW(NULL, TRUE, NULL);
    }

    if (g_hWakeTimer == NULL) {
        LeaveCriticalSection(&g_csTimer);
        return FALSE;
    }

    /*
     * Negative value specifies relative time in 100-nanosecond units.
     * 1 second = 10,000,000 units. Clamp to 10 years max to prevent 64-bit overflow.
     */
    if (seconds > 315360000.0) {
        seconds = 315360000.0;
    }
    LARGE_INTEGER dueTime;
    LONGLONG units = (LONGLONG)(seconds * 10000000.0);
    if (units < 1) {
        units = 1;
    }
    dueTime.QuadPart = -units;

    /*
     * fResume = TRUE: Restores the system to normal power state if suspended!
     * This wakes the PC via hardware RTC interrupt even in S3/Modern Standby.
     */
    BOOL success = SetWaitableTimer(
        g_hWakeTimer,
        &dueTime,
        0,          /* Period = 0 (one-shot) */
        NULL,       /* Completion routine */
        NULL,       /* Arg to completion routine */
        TRUE        /* fResume = TRUE: Wake system! */
    );

    if (!success) {
        CloseHandle(g_hWakeTimer);
        g_hWakeTimer = NULL;
        LeaveCriticalSection(&g_csTimer);
        return FALSE;
    }

    LeaveCriticalSection(&g_csTimer);
    return TRUE;
}

POWER_CORE_API BOOL NativeCancelHardwareWakeTimer(void) {
    EnsureCriticalSectionInitialized();
    EnterCriticalSection(&g_csTimer);

    BOOL result = TRUE;
    if (g_hWakeTimer != NULL) {
        CancelWaitableTimer(g_hWakeTimer);
        CloseHandle(g_hWakeTimer);
        g_hWakeTimer = NULL;
    } else {
        result = FALSE;
    }

    LeaveCriticalSection(&g_csTimer);
    return result;
}

/* --------------------------------------------------------------------------
 * 2. Power & Execution State Management (절전 및 디스플레이 꺼짐 방지)
 * -------------------------------------------------------------------------- */

POWER_CORE_API BOOL NativeSetSleepPrevention(int prevent_sleep, int keep_display) {
    EXECUTION_STATE esFlags = ES_CONTINUOUS;

    if (prevent_sleep) {
        esFlags |= ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED;
    }
    if (keep_display) {
        esFlags |= ES_DISPLAY_REQUIRED;
    }

    EXECUTION_STATE previous = SetThreadExecutionState(esFlags);
    return (previous != 0);
}

/* --------------------------------------------------------------------------
 * 3. 100% Silent Native Process Tree Killer (무음 다계층 프로세스 킬러)
 * -------------------------------------------------------------------------- */

static BOOL TerminateSingleProcessSilent(DWORD pid) {
    if (pid == 0 || pid == 4) {
        return FALSE; /* Protect Idle and System PID */
    }
    HANDLE hProc = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (hProc == NULL) {
        return FALSE;
    }
    BOOL ok = TerminateProcess(hProc, 1);
    CloseHandle(hProc);
    return ok;
}

/* High-efficiency single-snapshot recursive process tree collection with cycle guard */
typedef struct {
    DWORD pid;
    DWORD parentPid;
    BYTE visited;
} ProcNode;

static void CollectSubtree(DWORD currentPid, ProcNode* allNodes, int totalNodes, DWORD* outPids, int maxPids, int* outCount, int depth) {
    if (depth > 64) {
        return; /* Guard against extreme/malformed process recursion depth */
    }
    for (int i = 0; i < totalNodes; i++) {
        if (!allNodes[i].visited && allNodes[i].parentPid == currentPid && allNodes[i].pid != currentPid) {
            allNodes[i].visited = 1;
            if (*outCount < maxPids) {
                outPids[(*outCount)++] = allNodes[i].pid;
                CollectSubtree(allNodes[i].pid, allNodes, totalNodes, outPids, maxPids, outCount, depth + 1);
            }
        }
    }
}

static void CollectChildPids(DWORD parentPid, DWORD* pids, int maxPids, int* count) {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) {
        return;
    }

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    int capacity = 1024;
    ProcNode* allNodes = (ProcNode*)malloc(sizeof(ProcNode) * (size_t)capacity);
    int totalNodes = 0;

    if (allNodes != NULL && Process32FirstW(hSnap, &pe)) {
        do {
            if (totalNodes >= capacity && capacity < 16384) {
                int newCap = capacity * 2;
                ProcNode* grown = (ProcNode*)realloc(allNodes, sizeof(ProcNode) * (size_t)newCap);
                if (grown != NULL) {
                    allNodes = grown;
                    capacity = newCap;
                }
            }
            if (totalNodes < capacity) {
                allNodes[totalNodes].pid = pe.th32ProcessID;
                allNodes[totalNodes].parentPid = pe.th32ParentProcessID;
                allNodes[totalNodes].visited = (pe.th32ProcessID == parentPid) ? 1 : 0;
                totalNodes++;
            }
        } while (Process32NextW(hSnap, &pe));
    }
    CloseHandle(hSnap);

    if (allNodes != NULL) {
        CollectSubtree(parentPid, allNodes, totalNodes, pids, maxPids, count, 0);
        free(allNodes);
    }
}

POWER_CORE_API int NativeKillProcessTree(unsigned long root_pid) {
    if (root_pid <= 4) {
        return 0;
    }

    DWORD childPids[1024];
    int childCount = 0;

    CollectChildPids((DWORD)root_pid, childPids, 1024, &childCount);

    int killed = 0;
    /* Kill children first (bottom-up) */
    for (int i = childCount - 1; i >= 0; i--) {
        if (TerminateSingleProcessSilent(childPids[i])) {
            killed++;
        }
    }

    /* Terminate root process */
    if (TerminateSingleProcessSilent((DWORD)root_pid)) {
        killed++;
    }

    return killed;
}

POWER_CORE_API int NativeKillProcessByName(const wchar_t* process_name) {
    if (process_name == NULL || wcslen(process_name) == 0) {
        return 0;
    }

    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) {
        return 0;
    }

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    DWORD selfPid = GetCurrentProcessId();
    DWORD targetPids[256];
    int targetCount = 0;

    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (_wcsicmp(pe.szExeFile, process_name) == 0) {
                if (pe.th32ProcessID > 4 && pe.th32ProcessID != selfPid && targetCount < 256) {
                    targetPids[targetCount++] = pe.th32ProcessID;
                }
            }
        } while (Process32NextW(hSnap, &pe));
    }
    CloseHandle(hSnap);

    int killed = 0;
    for (int i = 0; i < targetCount; i++) {
        killed += NativeKillProcessTree(targetPids[i]);
    }

    return killed;
}
