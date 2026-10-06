/*
 * low_level_input_idle_native.c
 * PowerController Pure Custom Native Low-Level Input & Idle Time Telemetry (순수 창작 무동작/유휴 시간 정밀 감시기)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Queries GetLastInputInfo Win32 API to determine exact user inactivity milliseconds
 *  - Optional low-level keyboard & mouse hook telemetry
 *  - Enables ultra-precise auto-shutdown or sleep when system is idle for N minutes
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>

#define IDLE_API __declspec(dllexport)

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
    }
    return TRUE;
}

/*
 * Returns exact milliseconds elapsed since last user keyboard or mouse input
 */
IDLE_API DWORD NativeGetSystemIdleMilliseconds(void) {
    LASTINPUTINFO lii;
    lii.cbSize = sizeof(LASTINPUTINFO);
    lii.dwTime = 0;

    if (!GetLastInputInfo(&lii)) {
        return 0;
    }

    DWORD currentTick = GetTickCount();
    if (currentTick >= lii.dwTime) {
        return (currentTick - lii.dwTime);
    } else {
        /* TickCount wrap-around after ~49.7 days */
        return (0xFFFFFFFF - lii.dwTime) + currentTick;
    }
}

/*
 * Returns idle time in seconds
 */
IDLE_API double NativeGetSystemIdleSeconds(void) {
    DWORD ms = NativeGetSystemIdleMilliseconds();
    return (double)ms / 1000.0;
}

/*
 * Checks whether user has been inactive for more than target_seconds
 */
IDLE_API BOOL NativeIsSystemIdleFor(double target_seconds) {
    if (target_seconds <= 0.0) return FALSE;
    return (NativeGetSystemIdleSeconds() >= target_seconds);
}
