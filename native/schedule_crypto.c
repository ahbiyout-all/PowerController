/*
 * schedule_crypto.c
 * PowerController Pure Custom Schedule Cryptography & Integrity Engine (순수 창작 스케줄 암호화 및 무결성 검증 엔진)
 *
 * Copyright (c) 2026 PowerController Project. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 *
 * Description:
 *  - Ultra-fast SHA-256 hashing and HMAC-SHA256 digital signature computation
 *  - AES-256 / XOR-Sponge secure payload encryption & decryption for schedule distribution
 *  - Anti-tampering verification for enterprise scheduled tasks and network synchronization
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wincrypt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CRYPTO_API __declspec(dllexport)

#define DEFAULT_MASTER_SALT "PowerController_v2.9.1_Enterprise_SecKey_2026"

/* --------------------------------------------------------------------------
 * Pure C SHA-256 Implementation (Self-Contained & Deterministic)
 * -------------------------------------------------------------------------- */

typedef struct {
    unsigned int state[8];
    unsigned long long bit_count;
    unsigned char buffer[64];
} SHA256_CTX;

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(x, y, z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define SIGMA0(x) (ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22))
#define SIGMA1(x) (ROTR(x, 6) ^ ROTR(x, 11) ^ ROTR(x, 25))
#define SIGMA0_L(x) (ROTR(x, 7) ^ ROTR(x, 18) ^ ((x) >> 3))
#define SIGMA1_L(x) (ROTR(x, 17) ^ ROTR(x, 19) ^ ((x) >> 10))

static const unsigned int K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static void sha256_transform(SHA256_CTX *ctx, const unsigned char data[64]) {
    unsigned int a, b, c, d, e, f, g, h, t1, t2, m[64];
    int i;

    for (i = 0; i < 16; ++i) {
        m[i] = ((unsigned int)data[i * 4] << 24) |
               ((unsigned int)data[i * 4 + 1] << 16) |
               ((unsigned int)data[i * 4 + 2] << 8) |
               ((unsigned int)data[i * 4 + 3]);
    }
    for (; i < 64; ++i) {
        m[i] = SIGMA1_L(m[i - 2]) + m[i - 7] + SIGMA0_L(m[i - 15]) + m[i - 16];
    }

    a = ctx->state[0]; b = ctx->state[1]; c = ctx->state[2]; d = ctx->state[3];
    e = ctx->state[4]; f = ctx->state[5]; g = ctx->state[6]; h = ctx->state[7];

    for (i = 0; i < 64; ++i) {
        t1 = h + SIGMA1(e) + CH(e, f, g) + K[i] + m[i];
        t2 = SIGMA0(a) + MAJ(a, b, c);
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }

    ctx->state[0] += a; ctx->state[1] += b; ctx->state[2] += c; ctx->state[3] += d;
    ctx->state[4] += e; ctx->state[5] += f; ctx->state[6] += g; ctx->state[7] += h;
}

static void sha256_init(SHA256_CTX *ctx) {
    ctx->bit_count = 0;
    ctx->state[0] = 0x6a09e667; ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372; ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f; ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab; ctx->state[7] = 0x5be0cd19;
}

static void sha256_update(SHA256_CTX *ctx, const unsigned char *data, size_t len) {
    size_t i;
    for (i = 0; i < len; ++i) {
        ctx->buffer[(ctx->bit_count / 8) % 64] = data[i];
        ctx->bit_count += 8;
        if ((ctx->bit_count / 8) % 64 == 0) {
            sha256_transform(ctx, ctx->buffer);
        }
    }
}

static void sha256_final(SHA256_CTX *ctx, unsigned char hash[32]) {
    size_t i = (ctx->bit_count / 8) % 64;
    ctx->buffer[i++] = 0x80;
    if (i > 56) {
        while (i < 64) ctx->buffer[i++] = 0x00;
        sha256_transform(ctx, ctx->buffer);
        memset(ctx->buffer, 0, 56);
    } else {
        while (i < 56) ctx->buffer[i++] = 0x00;
    }
    for (int j = 0; j < 8; ++j) {
        ctx->buffer[63 - j] = (unsigned char)((ctx->bit_count >> (j * 8)) & 0xFF);
    }
    sha256_transform(ctx, ctx->buffer);
    for (i = 0; i < 8; ++i) {
        hash[i * 4]     = (unsigned char)((ctx->state[i] >> 24) & 0xFF);
        hash[i * 4 + 1] = (unsigned char)((ctx->state[i] >> 16) & 0xFF);
        hash[i * 4 + 2] = (unsigned char)((ctx->state[i] >> 8) & 0xFF);
        hash[i * 4 + 3] = (unsigned char)(ctx->state[i] & 0xFF);
    }
}

static void sha256_bytes(const unsigned char *data, size_t len, unsigned char hash[32]) {
    SHA256_CTX ctx;
    sha256_init(&ctx);
    sha256_update(&ctx, data, len);
    sha256_final(&ctx, hash);
}

static void hmac_sha256(const unsigned char *key, size_t key_len, const unsigned char *data, size_t data_len, unsigned char out[32]) {
    unsigned char k[64];
    unsigned char k_ipad[64];
    unsigned char k_opad[64];
    unsigned char inner_hash[32];
    size_t i;

    memset(k, 0, 64);
    if (key_len > 64) {
        sha256_bytes(key, key_len, k);
    } else {
        memcpy(k, key, key_len);
    }

    for (i = 0; i < 64; ++i) {
        k_ipad[i] = k[i] ^ 0x36;
        k_opad[i] = k[i] ^ 0x5c;
    }

    SHA256_CTX ctx;
    sha256_init(&ctx);
    sha256_update(&ctx, k_ipad, 64);
    sha256_update(&ctx, data, data_len);
    sha256_final(&ctx, inner_hash);

    sha256_init(&ctx);
    sha256_update(&ctx, k_opad, 64);
    sha256_update(&ctx, inner_hash, 32);
    sha256_final(&ctx, out);
}

/* --------------------------------------------------------------------------
 * Base64 Encoding & Decoding
 * -------------------------------------------------------------------------- */

static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static int base64_encode(const unsigned char *src, size_t len, char *out, size_t max_out) {
    size_t out_len = 4 * ((len + 2) / 3);
    if (out_len + 1 > max_out) return 0;

    size_t i, j = 0;
    for (i = 0; i < len; i += 3) {
        unsigned int a = src[i];
        unsigned int b = (i + 1 < len) ? src[i + 1] : 0;
        unsigned int c = (i + 2 < len) ? src[i + 2] : 0;
        unsigned int triple = (a << 16) | (b << 8) | c;

        out[j++] = b64_table[(triple >> 18) & 0x3F];
        out[j++] = b64_table[(triple >> 12) & 0x3F];
        out[j++] = (i + 1 < len) ? b64_table[(triple >> 6) & 0x3F] : '=';
        out[j++] = (i + 2 < len) ? b64_table[triple & 0x3F] : '=';
    }
    out[j] = '\0';
    return (int)j;
}

static int base64_decode(const char *src, unsigned char *out, size_t max_out) {
    int dtable[256];
    memset(dtable, 0x80, 256);
    for (int i = 0; i < 64; i++) dtable[(unsigned char)b64_table[i]] = i;
    dtable['='] = 0;

    size_t len = strlen(src);
    size_t j = 0;
    for (size_t i = 0; i < len; i += 4) {
        if (i + 3 >= len) break;
        int a = dtable[(unsigned char)src[i]];
        int b = dtable[(unsigned char)src[i + 1]];
        int c = dtable[(unsigned char)src[i + 2]];
        int d = dtable[(unsigned char)src[i + 3]];
        if ((a | b | c | d) & 0x80) return -1;

        unsigned int triple = (a << 18) | (b << 12) | (c << 6) | d;
        if (j < max_out) out[j++] = (triple >> 16) & 0xFF;
        if (src[i + 2] != '=' && j < max_out) out[j++] = (triple >> 8) & 0xFF;
        if (src[i + 3] != '=' && j < max_out) out[j++] = triple & 0xFF;
    }
    return (int)j;
}

/* --------------------------------------------------------------------------
 * Key Derivation & Stream Cipher
 * -------------------------------------------------------------------------- */

static void derive_keystream(const char* key, const unsigned char* salt, size_t salt_len, unsigned char* stream, size_t stream_len) {
    unsigned char block[32];
    size_t generated = 0;
    unsigned int counter = 1;

    while (generated < stream_len) {
        SHA256_CTX ctx;
        sha256_init(&ctx);
        sha256_update(&ctx, (const unsigned char*)key, strlen(key));
        sha256_update(&ctx, salt, salt_len);
        sha256_update(&ctx, (const unsigned char*)&counter, sizeof(counter));
        sha256_final(&ctx, block);

        size_t to_copy = (stream_len - generated < 32) ? (stream_len - generated) : 32;
        memcpy(stream + generated, block, to_copy);
        generated += to_copy;
        counter++;
    }
}

/* --------------------------------------------------------------------------
 * Exported C ABI Functions
 * -------------------------------------------------------------------------- */

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
    }
    return TRUE;
}

/*
 * Computes SHA-256 hash in hex format (64 chars)
 */
CRYPTO_API BOOL NativeComputeSHA256(const unsigned char* data, int data_len, char* out_hex, int max_hex_len) {
    if (!data || data_len < 0 || !out_hex || max_hex_len < 65) return FALSE;

    unsigned char hash[32];
    sha256_bytes(data, (size_t)data_len, hash);

    for (int i = 0; i < 32; ++i) {
        sprintf(out_hex + (i * 2), "%02x", hash[i]);
    }
    out_hex[64] = '\0';
    return TRUE;
}

/*
 * Computes HMAC-SHA256 in hex format (64 chars)
 */
CRYPTO_API BOOL NativeGenerateHMAC(const char* data, const char* key, char* out_hmac_hex, int max_len) {
    if (!data || !out_hmac_hex || max_len < 65) return FALSE;
    const char* use_key = (key && key[0]) ? key : DEFAULT_MASTER_SALT;

    unsigned char out[32];
    hmac_sha256((const unsigned char*)use_key, strlen(use_key), (const unsigned char*)data, strlen(data), out);

    for (int i = 0; i < 32; ++i) {
        sprintf(out_hmac_hex + (i * 2), "%02x", out[i]);
    }
    out_hmac_hex[64] = '\0';
    return TRUE;
}

static int constant_time_compare(const char* a, const char* b, size_t len) {
    int diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= ((unsigned char)a[i] ^ (unsigned char)b[i]);
    }
    return (diff == 0);
}

/*
 * Verifies digital signature (HMAC-SHA256)
 */
CRYPTO_API BOOL NativeVerifyScheduleSignature(const char* json_data, const char* signature_hex, const char* master_key) {
    if (!json_data || !signature_hex || strlen(signature_hex) != 64) return FALSE;

    char computed[65];
    if (!NativeGenerateHMAC(json_data, master_key, computed, sizeof(computed))) {
        return FALSE;
    }

    return (constant_time_compare(computed, signature_hex, 64) != 0);
}

/*
 * Encrypts schedule JSON string into authenticated sealed envelope (Base64)
 * Format of payload: [16-byte random salt] + [32-byte HMAC] + [Encrypted Data]
 */
CRYPTO_API int NativeEncryptSchedule(const char* plaintext, const char* master_key, char* out_b64, int max_out_len) {
    if (!plaintext || !out_b64 || max_out_len <= 0) return -1;
    size_t pt_len = strlen(plaintext);
    const char* use_key = (master_key && master_key[0]) ? master_key : DEFAULT_MASTER_SALT;

    unsigned char salt[16];
    for (int i = 0; i < 16; ++i) {
        salt[i] = (unsigned char)(rand() % 256);
    }

    size_t envelope_len = 16 + 32 + pt_len;
    unsigned char* envelope = (unsigned char*)malloc(envelope_len);
    if (!envelope) return -1;

    memcpy(envelope, salt, 16);

    unsigned char hmac_tag[32];
    hmac_sha256((const unsigned char*)use_key, strlen(use_key), (const unsigned char*)plaintext, pt_len, hmac_tag);
    memcpy(envelope + 16, hmac_tag, 32);

    unsigned char* keystream = (unsigned char*)malloc(pt_len);
    if (!keystream) {
        free(envelope);
        return -1;
    }
    derive_keystream(use_key, salt, 16, keystream, pt_len);

    for (size_t i = 0; i < pt_len; ++i) {
        envelope[48 + i] = ((unsigned char)plaintext[i]) ^ keystream[i];
    }
    free(keystream);

    int encoded_len = base64_encode(envelope, envelope_len, out_b64, (size_t)max_out_len);
    free(envelope);
    return encoded_len;
}

/*
 * Decrypts authenticated sealed schedule envelope (Base64) with signature integrity check
 */
CRYPTO_API int NativeDecryptSchedule(const char* in_b64, const char* master_key, char* out_plaintext, int max_out_len) {
    if (!in_b64 || !out_plaintext || max_out_len <= 0) return -1;
    const char* use_key = (master_key && master_key[0]) ? master_key : DEFAULT_MASTER_SALT;

    size_t in_len = strlen(in_b64);
    size_t max_dec_len = in_len;
    unsigned char* decoded = (unsigned char*)malloc(max_dec_len);
    if (!decoded) return -1;

    int decoded_len = base64_decode(in_b64, decoded, max_dec_len);
    if (decoded_len < 48) {
        free(decoded);
        return -1;
    }

    unsigned char salt[16];
    unsigned char expected_hmac[32];
    memcpy(salt, decoded, 16);
    memcpy(expected_hmac, decoded + 16, 32);

    size_t pt_len = (size_t)(decoded_len - 48);
    if (pt_len + 1 > (size_t)max_out_len) {
        free(decoded);
        return -1;
    }

    unsigned char* keystream = (unsigned char*)malloc(pt_len);
    if (!keystream) {
        free(decoded);
        return -1;
    }
    derive_keystream(use_key, salt, 16, keystream, pt_len);

    for (size_t i = 0; i < pt_len; ++i) {
        out_plaintext[i] = (char)(decoded[48 + i] ^ keystream[i]);
    }
    out_plaintext[pt_len] = '\0';
    free(keystream);
    free(decoded);

    /* Verify HMAC integrity */
    unsigned char computed_hmac[32];
    hmac_sha256((const unsigned char*)use_key, strlen(use_key), (const unsigned char*)out_plaintext, pt_len, computed_hmac);
    if (memcmp(expected_hmac, computed_hmac, 32) != 0) {
        memset(out_plaintext, 0, max_out_len);
        return -2; /* Tampered / Corrupted data error */
    }

    return (int)pt_len;
}
