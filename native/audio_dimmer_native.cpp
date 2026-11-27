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
    { 0xBCDE0395, 0xE52F, 0x467C, { 0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E } };
static const GUID IID_IMMDeviceEnumerator_Custom = 
    { 0xA95664D2, 0x9614, 0x4F35, { 0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6 } };
static const GUID IID_IAudioEndpointVolume_Custom = 
    { 0x5CDF2C82, 0x841E, 0x4546, { 0x97, 0x22, 0x0C, 0xF7, 0x40, 0x78, 0x22, 0x9A } };

struct ScopedAudioCom {
    BOOL need_uninit;
    ScopedAudioCom() : need_uninit(FALSE) {
        HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
        if (hr == RPC_E_CHANGED_MODE) {
            hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
        }
        if (hr == S_OK || hr == S_FALSE) {
            need_uninit = TRUE;
        }
    }
    ~ScopedAudioCom() {
        if (need_uninit) {
            CoUninitialize();
            need_uninit = FALSE;
        }
    }
};

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
    }
    return TRUE;
}

static IAudioEndpointVolume* GetMasterAudioVolumeEndpoint(void) {
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
    ScopedAudioCom com;
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return -1.0f;

    float currentVol = 0.0f;
    HRESULT hr = pVol->GetMasterVolumeLevelScalar(&currentVol);
    pVol->Release();
    return SUCCEEDED(hr) ? currentVol : -1.0f;
}

AUDIO_API BOOL NativeSetMasterVolume(float level_scalar) {
    if (level_scalar < 0.0f) level_scalar = 0.0f;
    if (level_scalar > 1.0f) level_scalar = 1.0f;

    ScopedAudioCom com;
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return FALSE;

    HRESULT hr = pVol->SetMasterVolumeLevelScalar(level_scalar, NULL);
    pVol->Release();
    return SUCCEEDED(hr);
}

AUDIO_API BOOL NativeSetMasterMute(BOOL mute) {
    ScopedAudioCom com;
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return FALSE;

    HRESULT hr = pVol->SetMute(mute ? TRUE : FALSE, NULL);
    pVol->Release();
    return SUCCEEDED(hr);
}

/*
 * Smooth Sigmoid/Cosine Fade-out of Audio Volume over fade_ms milliseconds
 * Reuses a single COM endpoint and QueryPerformanceCounter wall clock.
 */
AUDIO_API BOOL NativeFadeMasterVolume(float target_scalar, int fade_ms) {
    if (target_scalar < 0.0f) target_scalar = 0.0f;
    if (target_scalar > 1.0f) target_scalar = 1.0f;

    ScopedAudioCom com;
    IAudioEndpointVolume* pVol = GetMasterAudioVolumeEndpoint();
    if (!pVol) return FALSE;

    if (fade_ms <= 0) {
        HRESULT hr = pVol->SetMasterVolumeLevelScalar(target_scalar, NULL);
        pVol->Release();
        return SUCCEEDED(hr);
    }

    float startVol = 0.0f;
    if (FAILED(pVol->GetMasterVolumeLevelScalar(&startVol))) {
        pVol->Release();
        return FALSE;
    }

    LARGE_INTEGER freq, tStart, tNow;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&tStart);
    double targetDurationSec = (double)fade_ms / 1000.0;

    while (true) {
        QueryPerformanceCounter(&tNow);
        double elapsedSec = (double)(tNow.QuadPart - tStart.QuadPart) / (double)freq.QuadPart;
        double progress = elapsedSec / targetDurationSec;
        if (progress >= 1.0) {
            break;
        }
        double smoothFactor = 0.5 * (1.0 - cos(progress * 3.14159265358979323846));
        float currentTarget = startVol + (target_scalar - startVol) * (float)smoothFactor;
        pVol->SetMasterVolumeLevelScalar(currentTarget, NULL);
        Sleep(15);
    }

    HRESULT hrFinal = pVol->SetMasterVolumeLevelScalar(target_scalar, NULL);
    pVol->Release();
    return SUCCEEDED(hrFinal);
}
