/*
 * audio_dimmer_native.cpp
 * PowerController Pure Custom Native Audio Volume Dimmer Engine (순수 창작 Core Audio 음량 감쇠/페이드 엔진)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Direct Windows Core Audio COM interface (IMMDeviceEnumerator & IAudioEndpointVolume)
 *  - Smooth Sigmoid / Linear volume fade-out prior to power shutdown or sleep
 *  - Immediate mute / unmute toggle with zero external dependencies or C# / PowerShell overhead
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <math.h>

#define AUDIO_API extern "C" __declspec(dllexport)

static const GUID CLSID_MMDeviceEnumerator_Custom = 
    { 0xBCDE0380, 0x1D2D, 0x4628, { 0x8B, 0x60, 0x93, 0x1C, 0xBA, 0x34, 0x0E, 0x34 } };
static const GUID IID_IMMDeviceEnumerator_Custom = 
    { 0xA95664D2, 0x9614, 0x4F35, { 0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6 } };
static const GUID IID_IAudioEndpointVolume_Custom = 
    { 0x5CDF2C82, 0x841E, 0x4546, { 0x97, 0x22, 0x0C, 0xF7, 0x40, 0x78, 0x22, 0x9A } };

static BOOL g_AudioComInitialized = FALSE;

static void EnsureAudioComInitialized(void) {
    if (!g_AudioComInitialized) {
        HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
        if (hr == S_OK || hr == S_FALSE) {
            g_AudioComInitialized = TRUE;
        }
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsureAudioComInitialized();
            break;
        case DLL_PROCESS_DETACH:
            if (g_AudioComInitialized) {
                CoUninitialize();
                g_AudioComInitialized = FALSE;
            }
            break;
    }
    return TRUE;
}

static IAudioEndpointVolume* GetMasterAudioVolumeEndpoint(void) {
    EnsureAudioComInitialized();
    IMMDeviceEnumerator* pEnumerator = NULL;
    IMMDevice* pDevice = NULL;
    IAudioEndpointVolume* pVolume = NULL;

    HRESULT hr = CoCreateInstance(
        CLSID_MMDeviceEnumerator_Custom,
        NULL,
        CLSCTX_INPROC_SERVER,
        IID_IMMDeviceEnumerator_Custom,
        (void**)&pEnumerator
    );

    if (FAILED(hr) || !pEnumerator) return NULL;

    hr = pEnumerator->GetDefaultAudioEndpoint(eRender, eMultimedia, &pDevice);
    pEnumerator->Release();
    if (FAILED(hr) || !pDevice) return NULL;

    hr = pDevice->Activate(IID_IAudioEndpointVolume_Custom, CLSCTX_INPROC_SERVER, NULL, (void**)&pVolume);
    pDevice->Release();
    if (FAILED(hr) || !pVolume) return NULL;

    return pVolume;
}

AUDIO_API float NativeGetMasterVolume(void) {
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return -1.0f;

    float currentVol = 0.0f;
    pVol->GetMasterVolumeLevelScalar(&currentVol);
    pVol->Release();
    return currentVol;
}

AUDIO_API BOOL NativeSetMasterVolume(float level_scalar) {
    if (level_scalar < 0.0f) level_scalar = 0.0f;
    if (level_scalar > 1.0f) level_scalar = 1.0f;

    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return FALSE;

    HRESULT hr = pVol->SetMasterVolumeLevelScalar(level_scalar, NULL);
    pVol->Release();
    return SUCCEEDED(hr);
}

AUDIO_API BOOL NativeSetMasterMute(BOOL mute) {
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return FALSE;

    HRESULT hr = pVol->SetMute(mute ? TRUE : FALSE, NULL);
    pVol->Release();
    return SUCCEEDED(hr);
}

/*
 * Smooth Sigmoid Fade-out of Audio Volume over fade_ms milliseconds
 */
AUDIO_API BOOL NativeFadeMasterVolume(float target_scalar, int fade_ms) {
    if (fade_ms <= 0) {
        return NativeSetMasterVolume(target_scalar);
    }

    float startVol = NativeGetMasterVolume();
    if (startVol < 0.0f) return FALSE;

    int steps = fade_ms / 20; // 50 updates per second
    if (steps <= 0) steps = 1;
    int stepSleep = fade_ms / steps;

    for (int i = 1; i <= steps; i++) {
        float progress = (float)i / (float)steps;
        /* Cosine smooth interpolation */
        float smoothFactor = 0.5f * (1.0f - (float)cos(progress * 3.14159265358979323846));
        float currentTarget = startVol + (target_scalar - startVol) * smoothFactor;
        NativeSetMasterVolume(currentTarget);
        Sleep(stepSleep);
    }

    return NativeSetMasterVolume(target_scalar);
}
