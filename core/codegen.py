C_TEMPLATE = r"""#define _GNU_SOURCE
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include <unistd.h>
#include <signal.h>

#define ZIP_RAW_LEN ((size_t)__ZIP_LEN__ULL)

static const char BUNDLE[] =
__BUNDLE_LITERAL__;

static char g_tmpzip[1024];

static void zora_cleanup(void) {
    if (g_tmpzip[0] != '\0') unlink(g_tmpzip);
}

static void zora_signal_handler(int sig) {
    zora_cleanup();
    _exit(128 + sig);
}

static int b64val(unsigned char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

static unsigned char *b64decode(const char *data, size_t len, size_t *out_len) {
    unsigned char *out = (unsigned char *)malloc(len / 4 * 3 + 4);
    if (!out) return NULL;

    unsigned int val = 0;
    int valb = -8;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        int c = b64val((unsigned char)data[i]);
        if (c < 0) continue;
        val = (val << 6) | (unsigned int)c;
        valb += 6;
        if (valb >= 0) {
            out[j++] = (unsigned char)((val >> valb) & 0xFF);
            valb -= 8;
        }
    }
    *out_len = j;
    return out;
}

static unsigned char *zora_inflate(const unsigned char *data, size_t len, size_t raw_len) {
    unsigned char *dest = (unsigned char *)malloc(raw_len ? raw_len : 1);
    if (!dest) return NULL;

    uLongf out_len = (uLongf)raw_len;
    if (uncompress(dest, &out_len, data, (uLong)len) != Z_OK || (size_t)out_len != raw_len) {
        free(dest);
        return NULL;
    }
    return dest;
}

static int zora_write_all(int fd, const unsigned char *buf, size_t len) {
    size_t done = 0;
    while (done < len) {
        ssize_t n = write(fd, buf + done, len - done);
        if (n < 0) return -1;
        done += (size_t)n;
    }
    return 0;
}

static int zora_config_fail(PyConfig *config, PyStatus status, const char *what) {
    fprintf(stderr, "[zora] %s: %s\n", what, status.err_msg ? status.err_msg : "unknown error");
    PyConfig_Clear(config);
    return 1;
}

static int zora_py_fail(const char *what) {
    fprintf(stderr, "[zora] %s\n", what);
    if (PyErr_Occurred()) PyErr_Print();
    Py_FinalizeEx();
    return 1;
}

int main(int argc, char *argv[]) {
    signal(SIGINT, zora_signal_handler);
    signal(SIGTERM, zora_signal_handler);
    atexit(zora_cleanup);

    size_t enc_len = 0;
    unsigned char *decoded = b64decode(BUNDLE, sizeof(BUNDLE) - 1, &enc_len);
    if (!decoded) { fprintf(stderr, "[zora] decode failed\n"); return 1; }

    unsigned char *zipdata = zora_inflate(decoded, enc_len, ZIP_RAW_LEN);
    free(decoded);
    if (!zipdata) { fprintf(stderr, "[zora] decompress failed\n"); return 1; }

    const char *tmpdir = getenv("TMPDIR");
    if (!tmpdir || tmpdir[0] == '\0') tmpdir = "__PYHOME_PLAIN__/tmp";
    if (access(tmpdir, W_OK) != 0) tmpdir = "/tmp";

    int n = snprintf(g_tmpzip, sizeof(g_tmpzip), "%s/zora_XXXXXX.zip", tmpdir);
    if (n < 0 || (size_t)n >= sizeof(g_tmpzip)) {
        free(zipdata);
        g_tmpzip[0] = '\0';
        fprintf(stderr, "[zora] temp path too long (tmpdir=%s)\n", tmpdir);
        return 1;
    }

    int fd = mkstemps(g_tmpzip, 4);
    if (fd < 0) {
        free(zipdata);
        g_tmpzip[0] = '\0';
        fprintf(stderr, "[zora] mkstemps failed (tmpdir=%s)\n", tmpdir);
        return 1;
    }

    int write_rc = zora_write_all(fd, zipdata, ZIP_RAW_LEN);
    int close_rc = close(fd);
    free(zipdata);
    if (write_rc != 0 || close_rc != 0) {
        fprintf(stderr, "[zora] failed to write temp bundle\n");
        return 1;
    }

    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    config.parse_argv = 0;

__ISOLATED_BLOCK__
    PyStatus status = PyConfig_SetString(&config, &config.home, __PYHOME_WIDE__);
    if (PyStatus_Exception(status)) return zora_config_fail(&config, status, "set home failed");

    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) return zora_config_fail(&config, status, "set argv failed");

    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) {
        fprintf(stderr, "[zora] python init failed: %s\n", status.err_msg ? status.err_msg : "unknown error");
        return 1;
    }

    PyObject *sys_path = PySys_GetObject("path");
    PyObject *zip_str = PyUnicode_FromString(g_tmpzip);
    if (!sys_path || !zip_str || PyList_Insert(sys_path, 0, zip_str) != 0) {
        Py_XDECREF(zip_str);
        return zora_py_fail("failed to register bundle on sys.path");
    }
    Py_DECREF(zip_str);

    PyObject *zipimport_mod = PyImport_ImportModule("zipimport");
    if (!zipimport_mod) return zora_py_fail("zipimport unavailable");
    PyObject *importer_cls = PyObject_GetAttrString(zipimport_mod, "zipimporter");
    Py_DECREF(zipimport_mod);
    if (!importer_cls) return zora_py_fail("zipimporter unavailable");

    PyObject *zip_path_obj = PyUnicode_FromString(g_tmpzip);
    PyObject *importer = zip_path_obj ? PyObject_CallOneArg(importer_cls, zip_path_obj) : NULL;
    Py_XDECREF(zip_path_obj);
    Py_DECREF(importer_cls);
    if (!importer) return zora_py_fail("cannot open bundle");

    PyObject *main_code = PyObject_CallMethod(importer, "get_code", "s", "__main__");
    Py_DECREF(importer);
    if (!main_code) return zora_py_fail("bundle has no __main__");

    PyObject *main_mod = PyImport_AddModule("__main__");
    PyObject *main_dict = main_mod ? PyModule_GetDict(main_mod) : NULL;
    if (!main_dict) {
        Py_DECREF(main_code);
        return zora_py_fail("cannot access __main__");
    }

    PyObject *zip_path_str = PyUnicode_FromString(g_tmpzip);
    PyObject *empty_str = PyUnicode_FromString("");
    if (zip_path_str) PyDict_SetItemString(main_dict, "__file__", zip_path_str);
    PyDict_SetItemString(main_dict, "__spec__", Py_None);
    PyDict_SetItemString(main_dict, "__loader__", Py_None);
    if (empty_str) PyDict_SetItemString(main_dict, "__package__", empty_str);
    Py_XDECREF(empty_str);
    Py_XDECREF(zip_path_str);

    PyObject *result = PyEval_EvalCode(main_code, main_dict, main_dict);
    Py_DECREF(main_code);

    int exit_code = 0;
    if (!result) {
        PyErr_Print();
        exit_code = 1;
    } else {
        Py_DECREF(result);
    }

    if (Py_FinalizeEx() < 0 && exit_code == 0) exit_code = 120;
    return exit_code;
}
"""

ISOLATED_BLOCK = (
    "    config.site_import = 0;\n"
    "    config.user_site_directory = 0;\n"
    "    config.use_environment = 0;\n"
)

CHUNK_WIDTH = 4000


def c_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def chunk_c_literal(payload: str, width: int = CHUNK_WIDTH) -> str:
    chunks = [payload[i:i + width] for i in range(0, len(payload), width)] or [""]
    return "\n".join(f'    "{c_escape(chunk)}"' for chunk in chunks)


def generate_c_stub(encoded_zip: str, zip_len: int, prefix: str, isolated: bool = False) -> str:
    bundle_literal = chunk_c_literal(encoded_zip) + ";"
    isolated_block = ISOLATED_BLOCK if isolated else ""
    pyhome_wide = 'L"' + c_escape(prefix) + '"'

    code = C_TEMPLATE
    code = code.replace("__BUNDLE_LITERAL__", bundle_literal)
    code = code.replace("__ZIP_LEN__", str(zip_len))
    code = code.replace("__ISOLATED_BLOCK__", isolated_block)
    code = code.replace("__PYHOME_WIDE__", pyhome_wide)
    code = code.replace("__PYHOME_PLAIN__", c_escape(prefix))
    return code
