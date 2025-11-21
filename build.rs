fn main() {
    // Keep extension-module link flags for the cdylib artifact.
    pyo3_build_config::add_extension_module_link_args();

    // Link tests/binaries against the discovered Python shared library so
    // `cargo test` works without extra environment flags.
    let cfg = pyo3_build_config::get();
    if let Some(lib_dir) = &cfg.lib_dir {
        println!("cargo:rustc-link-search=native={lib_dir}");
    }
    if let Some(lib_name) = &cfg.lib_name {
        println!("cargo:rustc-link-lib={lib_name}");
    }
    if let Some(prefix) = &cfg.python_framework_prefix {
        println!("cargo:rustc-link-arg=-Wl,-rpath,{prefix}");
    }
}
