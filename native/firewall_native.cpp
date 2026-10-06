/*
 * firewall_native.cpp
 * PowerController Pure Custom Native Windows Firewall COM Controller (순수 창작 네이티브 방화벽 COM 제어기)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Direct INetFwPolicy2 / INetFwRules COM interface transactions without spawning netsh.exe
 *  - Sub-50ms batch registration & deletion of application & port rules
 *  - Eliminates console flickering, UAC delay, and CLI execution bottlenecks
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <netfw.h>
#include <objbase.h>
#include <oleauto.h>
#include <stdio.h>
#include <wchar.h>

#define FIREWALL_API extern "C" __declspec(dllexport)

/* Direct GUID specifications for guaranteed compilation across GCC, Clang, and MSVC */
static const GUID CLSID_NetFwPolicy2_Custom = 
    { 0xE2B3C97F, 0x6AE1, 0x41AC, { 0x81, 0x7A, 0xF6, 0xF9, 0x21, 0x66, 0xD7, 0xDD } };
static const GUID IID_INetFwPolicy2_Custom = 
    { 0x98325047, 0xC671, 0x4144, { 0x8D, 0x81, 0xDE, 0xFC, 0xD7, 0x6F, 0x16, 0x47 } };
static const GUID CLSID_NetFwRule_Custom = 
    { 0x2C593F99, 0xDC94, 0x42B5, { 0xAB, 0x7F, 0x44, 0xA3, 0x25, 0x85, 0x46, 0x11 } };
static const GUID IID_INetFwRule_Custom = 
    { 0xAF230244, 0xBCE3, 0x4585, { 0x8E, 0xC0, 0xAE, 0x81, 0x37, 0xCE, 0x17, 0x7B } };

static BOOL g_ComInitialized = FALSE;

static void EnsureComInitialized(void) {
    if (!g_ComInitialized) {
        HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
        if (hr == S_OK || hr == S_FALSE) {
            g_ComInitialized = TRUE;
        }
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hinstDLL);
            EnsureComInitialized();
            break;
        case DLL_PROCESS_DETACH:
            if (g_ComInitialized) {
                CoUninitialize();
                g_ComInitialized = FALSE;
            }
            break;
    }
    return TRUE;
}

static INetFwPolicy2* GetPolicyInstance(void) {
    EnsureComInitialized();
    INetFwPolicy2* pPolicy = NULL;
    HRESULT hr = CoCreateInstance(
        CLSID_NetFwPolicy2_Custom,
        NULL,
        CLSCTX_INPROC_SERVER,
        IID_INetFwPolicy2_Custom,
        (void**)&pPolicy
    );
    if (FAILED(hr)) {
        return NULL;
    }
    return pPolicy;
}

static BOOL DeleteRuleInternal(INetFwRules* pFwRules, const wchar_t* rule_name) {
    if (!pFwRules || !rule_name || wcslen(rule_name) == 0) {
        return FALSE;
    }
    BSTR bstrName = SysAllocString(rule_name);
    HRESULT hr = pFwRules->Remove(bstrName);
    SysFreeString(bstrName);
    return SUCCEEDED(hr);
}

static BOOL AddApplicationRuleInternal(INetFwRules* pFwRules, const wchar_t* rule_name, const wchar_t* exe_path, int direction) {
    if (!pFwRules || !rule_name || !exe_path) {
        return FALSE;
    }

    INetFwRule* pRule = NULL;
    HRESULT hr = CoCreateInstance(
        CLSID_NetFwRule_Custom,
        NULL,
        CLSCTX_INPROC_SERVER,
        IID_INetFwRule_Custom,
        (void**)&pRule
    );
    if (FAILED(hr) || !pRule) {
        return FALSE;
    }

    BSTR bstrName = SysAllocString(rule_name);
    BSTR bstrApp = SysAllocString(exe_path);
    BSTR bstrDesc = SysAllocString(L"PowerController Suite Automated Firewall Exception");

    pRule->put_Name(bstrName);
    pRule->put_Description(bstrDesc);
    pRule->put_ApplicationName(bstrApp);
    pRule->put_Direction(direction == 2 ? NET_FW_RULE_DIR_OUT : NET_FW_RULE_DIR_IN);
    pRule->put_Action(NET_FW_ACTION_ALLOW);
    pRule->put_Profiles(NET_FW_PROFILE2_ALL);
    pRule->put_Enabled(VARIANT_TRUE);

    hr = pFwRules->Add(pRule);

    SysFreeString(bstrName);
    SysFreeString(bstrApp);
    SysFreeString(bstrDesc);
    pRule->Release();

    return SUCCEEDED(hr);
}

static BOOL AddPortRuleInternal(INetFwRules* pFwRules, const wchar_t* rule_name, int protocol, const wchar_t* port_str, int direction) {
    if (!pFwRules || !rule_name || !port_str) {
        return FALSE;
    }

    INetFwRule* pRule = NULL;
    HRESULT hr = CoCreateInstance(
        CLSID_NetFwRule_Custom,
        NULL,
        CLSCTX_INPROC_SERVER,
        IID_INetFwRule_Custom,
        (void**)&pRule
    );
    if (FAILED(hr) || !pRule) {
        return FALSE;
    }

    BSTR bstrName = SysAllocString(rule_name);
    BSTR bstrPorts = SysAllocString(port_str);
    BSTR bstrDesc = SysAllocString(L"PowerController Suite Dedicated Port Exception");

    pRule->put_Name(bstrName);
    pRule->put_Description(bstrDesc);
    pRule->put_Protocol(protocol == 6 ? NET_FW_IP_PROTOCOL_TCP : NET_FW_IP_PROTOCOL_UDP);
    pRule->put_LocalPorts(bstrPorts);
    pRule->put_Direction(direction == 2 ? NET_FW_RULE_DIR_OUT : NET_FW_RULE_DIR_IN);
    pRule->put_Action(NET_FW_ACTION_ALLOW);
    pRule->put_Profiles(NET_FW_PROFILE2_ALL);
    pRule->put_Enabled(VARIANT_TRUE);

    hr = pFwRules->Add(pRule);

    SysFreeString(bstrName);
    SysFreeString(bstrPorts);
    SysFreeString(bstrDesc);
    pRule->Release();

    return SUCCEEDED(hr);
}

/* --------------------------------------------------------------------------
 * Exported C ABI Functions
 * -------------------------------------------------------------------------- */

FIREWALL_API BOOL NativeAddApplicationRule(const wchar_t* rule_name, const wchar_t* exe_path, int direction) {
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return FALSE;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return FALSE;
    }

    BOOL ok = AddApplicationRuleInternal(pRules, rule_name, exe_path, direction);

    pRules->Release();
    pPolicy->Release();
    return ok;
}

FIREWALL_API BOOL NativeAddPortRule(const wchar_t* rule_name, int protocol, const wchar_t* port_str, int direction) {
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return FALSE;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return FALSE;
    }

    BOOL ok = AddPortRuleInternal(pRules, rule_name, protocol, port_str, direction);

    pRules->Release();
    pPolicy->Release();
    return ok;
}

FIREWALL_API BOOL NativeDeleteRule(const wchar_t* rule_name) {
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return FALSE;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return FALSE;
    }

    BOOL ok = DeleteRuleInternal(pRules, rule_name);

    pRules->Release();
    pPolicy->Release();
    return ok;
}

FIREWALL_API BOOL NativeIsFirewallRulePresent(const wchar_t* rule_name) {
    if (!rule_name) return FALSE;
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return FALSE;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return FALSE;
    }

    BSTR bstrName = SysAllocString(rule_name);
    INetFwRule* pItem = NULL;
    hr = pRules->Item(bstrName, &pItem);
    SysFreeString(bstrName);

    BOOL found = FALSE;
    if (SUCCEEDED(hr) && pItem) {
        found = TRUE;
        pItem->Release();
    }

    pRules->Release();
    pPolicy->Release();
    return found;
}

/*
 * Batch register all PowerController and PowerNetworkScheduler rules in memory within ~0.05s
 */
FIREWALL_API int NativeBatchRegisterSuite(const wchar_t* target_dir, const wchar_t* version_str) {
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return -1;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return -1;
    }

    wchar_t ver[32];
    if (version_str && wcslen(version_str) > 0) {
        wcsncpy(ver, version_str, 31);
        ver[31] = L'\0';
    } else {
        wcscpy(ver, L"2.9.1");
    }

    /* Build executable paths */
    wchar_t mainExe[MAX_PATH];
    wchar_t pnsExe[MAX_PATH];
    if (target_dir && wcslen(target_dir) > 0) {
        _snwprintf(mainExe, MAX_PATH, L"%s\\PowerController.exe", target_dir);
        _snwprintf(pnsExe, MAX_PATH, L"%s\\PowerNetworkScheduler.exe", target_dir);
    } else {
        wcscpy(mainExe, L"PowerController.exe");
        wcscpy(pnsExe, L"PowerNetworkScheduler.exe");
    }

    /* List of rules to clean first */
    wchar_t cleanList[16][128];
    int cleanCount = 0;

    wcscpy(cleanList[cleanCount++], L"PowerController (Inbound)");
    wcscpy(cleanList[cleanCount++], L"PowerController (Outbound)");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s (Inbound)", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s (Outbound)", ver);
    wcscpy(cleanList[cleanCount++], L"PowerController");

    wcscpy(cleanList[cleanCount++], L"PowerNetworkScheduler (Inbound)");
    wcscpy(cleanList[cleanCount++], L"PowerNetworkScheduler (Outbound)");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerNetworkScheduler v%s (Inbound)", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerNetworkScheduler v%s (Outbound)", ver);

    wcscpy(cleanList[cleanCount++], L"PowerController TCP 9988");
    wcscpy(cleanList[cleanCount++], L"PowerController UDP 9985");
    wcscpy(cleanList[cleanCount++], L"PowerController UDP 9986");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s TCP 9988", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s UDP 9985", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s UDP 9986", ver);

    for (int i = 0; i < cleanCount; i++) {
        DeleteRuleInternal(pRules, cleanList[i]);
    }

    int registeredCount = 0;

    /* 1. Register PowerController.exe */
    if (GetFileAttributesW(mainExe) != INVALID_FILE_ATTRIBUTES) {
        if (AddApplicationRuleInternal(pRules, L"PowerController (Inbound)", mainExe, 1)) registeredCount++;
        if (AddApplicationRuleInternal(pRules, L"PowerController (Outbound)", mainExe, 2)) registeredCount++;
        
        wchar_t rNameIn[128], rNameOut[128];
        _snwprintf(rNameIn, 128, L"PowerController v%s (Inbound)", ver);
        _snwprintf(rNameOut, 128, L"PowerController v%s (Outbound)", ver);
        if (AddApplicationRuleInternal(pRules, rNameIn, mainExe, 1)) registeredCount++;
        if (AddApplicationRuleInternal(pRules, rNameOut, mainExe, 2)) registeredCount++;
    }

    /* 2. Register PowerNetworkScheduler.exe */
    if (GetFileAttributesW(pnsExe) != INVALID_FILE_ATTRIBUTES) {
        if (AddApplicationRuleInternal(pRules, L"PowerNetworkScheduler (Inbound)", pnsExe, 1)) registeredCount++;
        if (AddApplicationRuleInternal(pRules, L"PowerNetworkScheduler (Outbound)", pnsExe, 2)) registeredCount++;

        wchar_t rNameIn[128], rNameOut[128];
        _snwprintf(rNameIn, 128, L"PowerNetworkScheduler v%s (Inbound)", ver);
        _snwprintf(rNameOut, 128, L"PowerNetworkScheduler v%s (Outbound)", ver);
        if (AddApplicationRuleInternal(pRules, rNameIn, pnsExe, 1)) registeredCount++;
        if (AddApplicationRuleInternal(pRules, rNameOut, pnsExe, 2)) registeredCount++;
    }

    /* 3. Register Ports: TCP 9988, UDP 9985, UDP 9986 */
    if (AddPortRuleInternal(pRules, L"PowerController TCP 9988", 6, L"9988", 1)) registeredCount++;
    if (AddPortRuleInternal(pRules, L"PowerController UDP 9985", 17, L"9985", 1)) registeredCount++;
    if (AddPortRuleInternal(pRules, L"PowerController UDP 9986", 17, L"9986", 1)) registeredCount++;

    wchar_t rPortName[128];
    _snwprintf(rPortName, 128, L"PowerController v%s TCP 9988", ver);
    if (AddPortRuleInternal(pRules, rPortName, 6, L"9988", 1)) registeredCount++;

    _snwprintf(rPortName, 128, L"PowerController v%s UDP 9985", ver);
    if (AddPortRuleInternal(pRules, rPortName, 17, L"9985", 1)) registeredCount++;

    _snwprintf(rPortName, 128, L"PowerController v%s UDP 9986", ver);
    if (AddPortRuleInternal(pRules, rPortName, 17, L"9986", 1)) registeredCount++;

    pRules->Release();
    pPolicy->Release();
    return registeredCount;
}

/*
 * Batch remove all suite rules in memory
 */
FIREWALL_API int NativeBatchRemoveSuite(const wchar_t* version_str) {
    INetFwPolicy2* pPolicy = GetPolicyInstance();
    if (!pPolicy) return -1;

    INetFwRules* pRules = NULL;
    HRESULT hr = pPolicy->get_Rules(&pRules);
    if (FAILED(hr) || !pRules) {
        pPolicy->Release();
        return -1;
    }

    wchar_t ver[32];
    if (version_str && wcslen(version_str) > 0) {
        wcsncpy(ver, version_str, 31);
        ver[31] = L'\0';
    } else {
        wcscpy(ver, L"2.9.1");
    }

    wchar_t cleanList[16][128];
    int cleanCount = 0;

    wcscpy(cleanList[cleanCount++], L"PowerController (Inbound)");
    wcscpy(cleanList[cleanCount++], L"PowerController (Outbound)");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s (Inbound)", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s (Outbound)", ver);
    wcscpy(cleanList[cleanCount++], L"PowerController");

    wcscpy(cleanList[cleanCount++], L"PowerNetworkScheduler (Inbound)");
    wcscpy(cleanList[cleanCount++], L"PowerNetworkScheduler (Outbound)");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerNetworkScheduler v%s (Inbound)", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerNetworkScheduler v%s (Outbound)", ver);

    wcscpy(cleanList[cleanCount++], L"PowerController TCP 9988");
    wcscpy(cleanList[cleanCount++], L"PowerController UDP 9985");
    wcscpy(cleanList[cleanCount++], L"PowerController UDP 9986");
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s TCP 9988", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s UDP 9985", ver);
    _snwprintf(cleanList[cleanCount++], 128, L"PowerController v%s UDP 9986", ver);

    int removed = 0;
    for (int i = 0; i < cleanCount; i++) {
        if (DeleteRuleInternal(pRules, cleanList[i])) {
            removed++;
        }
    }

    pRules->Release();
    pPolicy->Release();
    return removed;
}
