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

static HMODULE g_hDxva2Lib = NULL;
static pfnGetNumberOfPhysicalMonitorsFromHMONITOR g_pfnGetNumMonitors = NULL;
static pfnGetPhysicalMonitorsFromHMONITOR g_pfnGetPhysicalMonitors = NULL;
static pfnDestroyPhysicalMonitors g_pfnDestroyPhysicalMonitors = NULL;
static pfnSetMonitorBrightness g_pfnSetMonitorBrightness = NULL;
static pfnGetMonitorBrightness g_pfnGetMonitorBrightness = NULL;

static void InitDxva2Functions(void) {
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
}

struct MonitorCallbackData {
    int target_brightness;
    int updated_count;
};

static BOOL CALLBACK MonitorEnumProc(HMONITOR hMonitor, HDC hdcMonitor, LPRECT lprcMonitor, LPARAM dwData) {
    MonitorCallbackData* pData = (MonitorCallbackData*)dwData;
    if (!g_pfnGetNumMonitors || !g_pfnGetPhysicalMonitors || !g_pfnSetMonitorBrightness) {
        return TRUE;
    }

    DWORD numPhysicalMonitors = 0;
    if (!g_pfnGetNumMonitors(hMonitor, &numPhysicalMonitors) || numPhysicalMonitors == 0) {
        return TRUE;
    }

    PHYSICAL_MONITOR* pPhysicalMonitors = (PHYSICAL_MONITOR*)malloc(sizeof(PHYSICAL_MONITOR) * numPhysicalMonitors);
    if (!pPhysicalMonitors) return TRUE;

    if (g_pfnGetPhysicalMonitors(hMonitor, numPhysicalMonitors, pPhysicalMonitors)) {
        for (DWORD i = 0; i < numPhysicalMonitors; i++) {
            if (g_pfnSetMonitorBrightness(pPhysicalMonitors[i].hPhysicalMonitor, (DWORD)pData->target_brightness)) {
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

DISPLAY_API int NativeSetHardwareBrightness(int brightness_percent) {
    if (brightness_percent < 0) brightness_percent = 0;
    if (brightness_percent > 100) brightness_percent = 100;

    InitDxva2Functions();
    if (!g_hDxva2Lib) return 0;

    MonitorCallbackData data;
    data.target_brightness = brightness_percent;
    data.updated_count = 0;

    EnumDisplayMonitors(NULL, NULL, MonitorEnumProc, (LPARAM)&data);
    return data.updated_count;
}
