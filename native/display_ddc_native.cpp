/*
 * display_ddc_native.cpp
 * PowerController Pure Custom Native Display DDC/CI Brightness Engine (순수 창작 하드웨어 모니터 밝기 절전 제어기)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Uses Dxva2.dll / HighLevelMonitorConfigurationAPI (SetMonitorBrightness)
 *  - Directly sets physical monitor backlight brightness (0~100%) for Smart Power Saving (<20% battery)
 *  - Saves up to 80% monitor backlight energy without software overlay tinting
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <physicalmonitorenumerationapi.h>
#include <highlevelmonitorconfigurationapi.h>
#include <stdio.h>

#define DISPLAY_API extern "C" __declspec(dllexport)

typedef BOOL (WINAPI *pfnGetNumberOfPhysicalMonitorsFromHMONITOR)(HMONITOR, LPDWORD);
typedef BOOL (WINAPI *pfnGetPhysicalMonitorsFromHMONITOR)(HMONITOR, DWORD, LPPHYSICAL_MONITOR);
typedef BOOL (WINAPI *pfnDestroyPhysicalMonitors)(DWORD, LPPHYSICAL_MONITOR);
typedef BOOL (WINAPI *pfnSetMonitorBrightness)(HANDLE, DWORD);
typedef BOOL (WINAPI *pfnGetMonitorBrightness)(HANDLE, LPDWORD, LPDWORD, LPDWORD);

static CRITICAL_SECTION g_csDxva;
static BOOL g_csDxvaInit = FALSE;
static HMODULE g_hDxva2Lib = NULL;
static pfnGetNumberOfPhysicalMonitorsFromHMONITOR g_pfnGetNumMonitors = NULL;
static pfnGetPhysicalMonitorsFromHMONITOR g_pfnGetPhysicalMonitors = NULL;
static pfnDestroyPhysicalMonitors g_pfnDestroyPhysicalMonitors = NULL;
static pfnSetMonitorBrightness g_pfnSetMonitorBrightness = NULL;
static pfnGetMonitorBrightness g_pfnGetMonitorBrightness = NULL;

static void EnsureDxvaCS(void) {
    if (!g_csDxvaInit) {
        InitializeCriticalSection(&g_csDxva);
        g_csDxvaInit = TRUE;
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsureDxvaCS();
            break;
        case DLL_PROCESS_DETACH:
            if (lpvReserved == NULL) {
                if (g_hDxva2Lib != NULL) {
                    FreeLibrary(g_hDxva2Lib);
                    g_hDxva2Lib = NULL;
                }
                if (g_csDxvaInit) {
                    DeleteCriticalSection(&g_csDxva);
                    g_csDxvaInit = FALSE;
                }
            }
            break;
    }
    return TRUE;
}

static BOOL InitDxva2Functions(void) {
    EnsureDxvaCS();
    EnterCriticalSection(&g_csDxva);
    if (g_hDxva2Lib == NULL) {
        g_hDxva2Lib = LoadLibraryA("dxva2.dll");
        if (g_hDxva2Lib != NULL) {
            g_pfnGetNumMonitors = (pfnGetNumberOfPhysicalMonitorsFromHMONITOR)GetProcAddress(g_hDxva2Lib, "GetNumberOfPhysicalMonitorsFromHMONITOR");
            g_pfnGetPhysicalMonitors = (pfnGetPhysicalMonitorsFromHMONITOR)GetProcAddress(g_hDxva2Lib, "GetPhysicalMonitorsFromHMONITOR");
            g_pfnDestroyPhysicalMonitors = (pfnDestroyPhysicalMonitors)GetProcAddress(g_hDxva2Lib, "DestroyPhysicalMonitors");
            g_pfnSetMonitorBrightness = (pfnSetMonitorBrightness)GetProcAddress(g_hDxva2Lib, "SetMonitorBrightness");
            g_pfnGetMonitorBrightness = (pfnGetMonitorBrightness)GetProcAddress(g_hDxva2Lib, "GetMonitorBrightness");
        }
    }
    BOOL ok = (g_hDxva2Lib != NULL && g_pfnGetNumMonitors && g_pfnGetPhysicalMonitors && g_pfnSetMonitorBrightness);
    LeaveCriticalSection(&g_csDxva);
    return ok;
}

struct MonitorCallbackData {
    int target_brightness;
    int updated_count;
    int read_brightness;
};

static BOOL CALLBACK MonitorEnumSetProc(HMONITOR hMonitor, HDC hdcMonitor, LPRECT lprcMonitor, LPARAM dwData) {
    MonitorCallbackData* pData = (MonitorCallbackData*)dwData;
    DWORD numPhysicalMonitors = 0;
    if (!g_pfnGetNumMonitors(hMonitor, &numPhysicalMonitors) || numPhysicalMonitors == 0) {
        return TRUE;
    }

    PHYSICAL_MONITOR* pPhysicalMonitors = (PHYSICAL_MONITOR*)malloc(sizeof(PHYSICAL_MONITOR) * numPhysicalMonitors);
    if (!pPhysicalMonitors) return TRUE;

    if (g_pfnGetPhysicalMonitors(hMonitor, numPhysicalMonitors, pPhysicalMonitors)) {
        for (DWORD i = 0; i < numPhysicalMonitors; i++) {
            DWORD hwTarget = (DWORD)pData->target_brightness;
            if (g_pfnGetMonitorBrightness) {
                DWORD dwMin = 0, dwCur = 0, dwMax = 100;
                if (g_pfnGetMonitorBrightness(pPhysicalMonitors[i].hPhysicalMonitor, &dwMin, &dwCur, &dwMax) && dwMax > dwMin) {
                    hwTarget = dwMin + ((dwMax - dwMin) * (DWORD)pData->target_brightness) / 100;
                }
            }
            if (g_pfnSetMonitorBrightness(pPhysicalMonitors[i].hPhysicalMonitor, hwTarget)) {
                pData->updated_count++;
            }
        }
        if (g_pfnDestroyPhysicalMonitors) {
            g_pfnDestroyPhysicalMonitors(numPhysicalMonitors, pPhysicalMonitors);
        }
    }
    free(pPhysicalMonitors);
    return TRUE;
}

static BOOL CALLBACK MonitorEnumGetProc(HMONITOR hMonitor, HDC hdcMonitor, LPRECT lprcMonitor, LPARAM dwData) {
    MonitorCallbackData* pData = (MonitorCallbackData*)dwData;
    if (!g_pfnGetMonitorBrightness) return FALSE;

    DWORD numPhysicalMonitors = 0;
    if (!g_pfnGetNumMonitors(hMonitor, &numPhysicalMonitors) || numPhysicalMonitors == 0) {
        return TRUE;
    }

    PHYSICAL_MONITOR* pPhysicalMonitors = (PHYSICAL_MONITOR*)malloc(sizeof(PHYSICAL_MONITOR) * numPhysicalMonitors);
    if (!pPhysicalMonitors) return TRUE;

    if (g_pfnGetPhysicalMonitors(hMonitor, numPhysicalMonitors, pPhysicalMonitors)) {
        for (DWORD i = 0; i < numPhysicalMonitors; i++) {
            DWORD dwMin = 0, dwCur = 0, dwMax = 100;
            if (g_pfnGetMonitorBrightness(pPhysicalMonitors[i].hPhysicalMonitor, &dwMin, &dwCur, &dwMax)) {
                if (dwMax > dwMin) {
                    pData->read_brightness = (int)(((dwCur - dwMin) * 100) / (dwMax - dwMin));
                } else {
                    pData->read_brightness = (int)dwCur;
                }
                break;
            }
        }
        if (g_pfnDestroyPhysicalMonitors) {
            g_pfnDestroyPhysicalMonitors(numPhysicalMonitors, pPhysicalMonitors);
        }
    }
    free(pPhysicalMonitors);
    return (pData->read_brightness < 0) ? TRUE : FALSE;
}

DISPLAY_API int NativeSetHardwareBrightness(int brightness_percent) {
    if (brightness_percent < 0) brightness_percent = 0;
    if (brightness_percent > 100) brightness_percent = 100;

    if (!InitDxva2Functions()) return 0;

    MonitorCallbackData data;
    data.target_brightness = brightness_percent;
    data.updated_count = 0;
    data.read_brightness = -1;

    EnumDisplayMonitors(NULL, NULL, MonitorEnumSetProc, (LPARAM)&data);
    return data.updated_count;
}

DISPLAY_API int NativeGetHardwareBrightness(void) {
    if (!InitDxva2Functions() || !g_pfnGetMonitorBrightness) return -1;

    MonitorCallbackData data;
    data.target_brightness = 0;
    data.updated_count = 0;
    data.read_brightness = -1;

    EnumDisplayMonitors(NULL, NULL, MonitorEnumGetProc, (LPARAM)&data);
    return data.read_brightness;
}
