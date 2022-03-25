# Components enabled if supported by target architecture:
%define gold_arches %{ix86} x86_64 %{arm} aarch64 %{power64}
%ifarch %{gold_arches}
  %bcond_without gold
%else
  %bcond_with gold
%endif

%bcond_with compat_build

%global _smp_mflags -j8

%global llvm_libdir %{_libdir}/%{name}
%global build_llvm_libdir %{buildroot}%{llvm_libdir}
#%%global rc_ver 6
%global baserelease 3
%global llvm_srcdir llvm-%{version}%{?rc_ver:rc%{rc_ver}}.src
%global maj_ver 11
%global min_ver 0
%global patch_ver 0

%if %{with compat_build}
%global pkg_name llvm%{maj_ver}.%{min_ver}
%global exec_suffix -%{maj_ver}.%{min_ver}
%global install_prefix %{_libdir}/%{name}
%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%global install_libdir %{install_prefix}/lib

%global pkg_bindir %{install_bindir}
%global pkg_includedir %{_includedir}/%{name}
%global pkg_libdir %{install_libdir}
%else
%global pkg_name llvm
%global install_prefix /usr
%global install_libdir %{_libdir}
%global pkg_libdir %{install_libdir}
%endif

%global build_install_prefix %{buildroot}%{install_prefix}

%if !0%{?rhel}
# libedit-devel is a buildroot-only package in RHEL8, so we can't have a
# any run-time depencies on it.
%global use_libedit 1
%endif

Name:		%{pkg_name}
Version:	%{maj_ver}.%{min_ver}.%{patch_ver}
Release:	%{baserelease}%{?rc_ver:.rc%{rc_ver}}%{?dist}
Summary:	The Low Level Virtual Machine

License:	NCSA
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}%{?rc_ver:-rc%{rc_ver}}/%{llvm_srcdir}.tar.xz
%if %{without compat_build}
Source1:	run-lit-tests
Source2:	lit.fedora.cfg.py
%endif

# Fix coreos-installer test crash on s390x (rhbz#1883457), https://reviews.llvm.org/D89034
Patch1:		0001-CMake-Split-static-library-exports-into-their-own-ex.patch
Patch2:		0001-CMake-Split-test-binary-exports-into-their-own-expor.patch

# RHEL-specific patches.
Patch101:      0001-Deactivate-markdown-doc.patch
Patch102:      error-opening-permission.patch

BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	cmake
BuildRequires:	ninja-build
BuildRequires:	zlib-devel
BuildRequires:	libffi-devel
BuildRequires:	ncurses-devel
BuildRequires:	python3-sphinx

%if !0%{?rhel}
BuildRequires: python3-recommonmark
%else
BuildRequires: pandoc
%endif

BuildRequires:	multilib-rpm-config
%if %{with gold}
BuildRequires:	binutils-devel
%endif
%ifarch %{valgrind_arches}
# Enable extra functionality when run the LLVM JIT under valgrind.
BuildRequires:	valgrind-devel
%endif
%if 0%{?use_libedit}
# LLVM's LineEditor library will use libedit if it is available.
BuildRequires:	libedit-devel
%endif
# We need python3-devel for pathfix.py.
BuildRequires:	python3-devel

Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

Provides:	llvm(major) = %{maj_ver}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages. The compiler infrastructure includes mirror sets of programming
tools as well as libraries with equivalent functionality.

%package devel
Summary:	Libraries and header files for LLVM
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
# The installed LLVM cmake files will add -ledit to the linker flags for any
# app that requires the libLLVMLineEditor, so we need to make sure
# libedit-devel is available.
%if 0%{?use_libedit}
Requires:	libedit-devel
%endif
# The installed cmake files reference binaries from llvm-test and llvm-static.
# We tried in the past to split the cmake exports for these binaries out into
# separate files, so that llvm-devel would not need to Require these packages,
# but this caused bugs (rhbz#1773678) and forced us to carry two non-upstream
# patches.
Requires:	llvm-static%{?_isa} = %{version}-%{release}
Requires:	llvm-test%{?_isa} = %{version}-%{release}


Requires(post):	%{_sbindir}/alternatives
Requires(postun):	%{_sbindir}/alternatives

Provides:	llvm-devel(major) = %{maj_ver}

%description devel
This package contains library and header files needed to develop new native
programs that use the LLVM infrastructure.

%package doc
Summary:	Documentation for LLVM
BuildArch:	noarch
Requires:	%{name} = %{version}-%{release}

%description doc
Documentation for the LLVM compiler infrastructure.

%package libs
Summary:	LLVM shared libraries

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package static
Summary:	LLVM static libraries
Conflicts:	%{name}-devel < 8

%description static
Static libraries for the LLVM compiler infrastructure.

%if %{without compat_build}

%package test
Summary:	LLVM regression tests
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
Requires:	python3-lit
# The regression tests need gold.
Requires:	binutils
# This is for llvm-config
Requires:	%{name}-devel%{?_isa} = %{version}-%{release}
# Bugpoint tests require gcc
Requires:	gcc
Requires:	findutils

Provides:	llvm-test(major) = %{maj_ver}

%description test
LLVM regression tests.

%package googletest
Summary: LLVM's modified googletest sources

%description googletest
LLVM's modified googletest sources.

%endif

%prep
%autosetup -n %{llvm_srcdir} -p2

pathfix.py -i %{__python3} -pn \
	test/BugPoint/compile-custom.ll.py \
	tools/opt-viewer/*.py \
	utils/update_cc_test_checks.py

# Convert markdown files to rst to cope with the absence of compatible md parser in rhel.
# The sed expression takes care of a slight difference between pandoc markdown and sphinx markdown.
%ifnarch loongarch64
find -name '*.md' | while read md; do sed -r -e 's/^( )*\* /\n\1\* /' ${md} | pandoc -f markdown -o ${md%.md}.rst  ; done
%endif

%build
mkdir -p _build
cd _build

%ifarch s390 %{arm} %ix86
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

# force off shared libs as cmake macros turns it on.
#
# -DCMAKE_INSTALL_RPATH=";" is a workaround for llvm manually setting the
# rpath of libraries and binaries.  llvm will skip the manual setting
# if CMAKE_INSTALL_RPATH is set to a value, but cmake interprets this value
# as nothing, so it sets the rpath to "" when installing.
%cmake .. -G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_INSTALL_RPATH=";" \
%ifarch s390 %{arm} %ix86
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if %{without compat_build}
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%endif
	\
	-DLLVM_TARGETS_TO_BUILD="X86;AMDGPU;PowerPC;NVPTX;SystemZ;AArch64;ARM;Mips;BPF;LoongArch" \
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
%if %{with gold}
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
%endif
	\
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	\
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	\
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	\
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	\
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
%if %{with compat_build}
	-DLLVM_INSTALL_UTILS:BOOL=OFF \
%else
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=%{_bindir} \
	-DLLVM_TOOLS_INSTALL_DIR:PATH=bin \
%endif
	\
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	\
%if %{without compat_build}
	-DLLVM_VERSION_SUFFIX='' \
%endif
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_DYLIB_EXPORT_ALL:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	\
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3

# Build libLLVM.so first.  This ensures that when libLLVM.so is linking, there
# are no other compile jobs running.  This will help reduce OOM errors on the
# builders without having to artificially limit the number of concurrent jobs.
%ninja_build LLVM
%ninja_build

%install
%ninja_install -C _build


%if %{without compat_build}
mkdir -p %{buildroot}/%{_bindir}
mv %{buildroot}/%{_bindir}/llvm-config %{buildroot}/%{_bindir}/llvm-config-%{__isa_bits}

# ghost presence
touch %{buildroot}%{_bindir}/llvm-config

# Fix some man pages
ln -s llvm-config.1 %{buildroot}%{_mandir}/man1/llvm-config-%{__isa_bits}.1
mv %{buildroot}%{_mandir}/man1/tblgen.1 %{buildroot}%{_mandir}/man1/llvm-tblgen.1

# Install binaries needed for lit tests
%global test_binaries llvm-isel-fuzzer llvm-opt-fuzzer

for f in %{test_binaries}
do
    install -m 0755 ./_build/bin/$f %{buildroot}%{_bindir}
done

# Remove testing of update utility tools
rm -rf test/tools/UpdateTestChecks

%multilib_fix_c_header --file %{_includedir}/llvm/Config/llvm-config.h

# Install libraries needed for unittests
%if 0%{?__isa_bits} == 64
%global build_libdir _build/lib64
%else
%global build_libdir _build/lib
%endif

install %{build_libdir}/libLLVMTestingSupport.a %{buildroot}%{_libdir}

%global install_srcdir %{buildroot}%{_datadir}/llvm/src
%global lit_cfg test/%{_arch}.site.cfg.py
%global lit_unit_cfg test/Unit/%{_arch}.site.cfg.py
%global lit_fedora_cfg %{_datadir}/llvm/lit.fedora.cfg.py

# Install gtest sources so clang can use them for gtest
install -d %{install_srcdir}
install -d %{install_srcdir}/utils/
cp -R utils/unittest %{install_srcdir}/utils/

# Clang needs these for running lit tests.
cp utils/update_cc_test_checks.py %{install_srcdir}/utils/
cp -R utils/UpdateTestChecks %{install_srcdir}/utils/

# One of the lit tests references this file
install -d %{install_srcdir}/docs/CommandGuide/
install -m 0644 docs/CommandGuide/dsymutil.rst %{install_srcdir}/docs/CommandGuide/

# Generate lit config files.  Strip off the last lines that initiates the
# test run, so we can customize the configuration.
head -n -2 _build/test/lit.site.cfg.py >> %{lit_cfg}
head -n -2 _build/test/Unit/lit.site.cfg.py >> %{lit_unit_cfg}

# Install custom fedora config file
cp %{SOURCE2} %{buildroot}%{lit_fedora_cfg}

# Patch lit config files to load custom fedora config:
for f in %{lit_cfg} %{lit_unit_cfg}; do
  echo "lit_config.load_config(config, '%{lit_fedora_cfg}')" >> $f
done

install -d %{buildroot}%{_libexecdir}/tests/llvm
install -m 0755 %{SOURCE1} %{buildroot}%{_libexecdir}/tests/llvm

# Install lit tests.  We need to put these in a tarball otherwise rpm will complain
# about some of the test inputs having the wrong object file format.
install -d %{buildroot}%{_datadir}/llvm/

# The various tar options are there to make sur the archive is the same on 32 and 64 bit arch, i.e.
# the archive creation is reproducible. Move arch-specific content out of the tarball
mv %{lit_cfg} %{install_srcdir}/%{_arch}.site.cfg.py
mv %{lit_unit_cfg} %{install_srcdir}/%{_arch}.Unit.site.cfg.py
tar --sort=name --mtime='UTC 2020-01-01' -c test/ | gzip -n > %{install_srcdir}/test.tar.gz

# Install the unit test binaries
mkdir -p %{build_llvm_libdir}
cp -R _build/unittests %{build_llvm_libdir}/
rm -rf `find %{build_llvm_libdir} -iname 'cmake*'`

# Install libraries used for testing
install -m 0755 %{build_libdir}/BugpointPasses.so %{buildroot}%{_libdir}
install -m 0755 %{build_libdir}/LLVMHello.so %{buildroot}%{_libdir}

# Install test inputs for PDB tests
echo "%{_datadir}/llvm/src/unittests/DebugInfo/PDB" > %{build_llvm_libdir}/unittests/DebugInfo/PDB/llvm.srcdir.txt
mkdir -p %{buildroot}%{_datadir}/llvm/src/unittests/DebugInfo/PDB/
cp -R unittests/DebugInfo/PDB/Inputs %{buildroot}%{_datadir}/llvm/src/unittests/DebugInfo/PDB/

%if %{with gold}
# Add symlink to lto plugin in the binutils plugin directory.
%{__mkdir_p} %{buildroot}%{_libdir}/bfd-plugins/
ln -s %{_libdir}/LLVMgold.so %{buildroot}%{_libdir}/bfd-plugins/
%endif

%else

# Add version suffix to binaries
mkdir -p %{buildroot}/%{_bindir}
for f in %{buildroot}/%{install_bindir}/*; do
  filename=`basename $f`
  ln -s ../../../%{install_bindir}/$filename %{buildroot}/%{_bindir}/$filename%{exec_suffix}
done

# Move header files
mkdir -p %{buildroot}/%{pkg_includedir}
ln -s ../../../%{install_includedir}/llvm %{buildroot}/%{pkg_includedir}/llvm
ln -s ../../../%{install_includedir}/llvm-c %{buildroot}/%{pkg_includedir}/llvm-c

# Fix multi-lib
mv %{buildroot}%{_bindir}/llvm-config{%{exec_suffix},%{exec_suffix}-%{__isa_bits}}
%multilib_fix_c_header --file %{install_includedir}/llvm/Config/llvm-config.h

# Create ld.so.conf.d entry
mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d
cat >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf << EOF
%{pkg_libdir}
EOF

# Add version suffix to man pages and move them to mandir.
mkdir -p %{buildroot}/%{_mandir}/man1
for f in %{build_install_prefix}/share/man/man1/*; do
  filename=`basename $f | cut -f 1 -d '.'`
  mv $f %{buildroot}%{_mandir}/man1/$filename%{exec_suffix}.1
done

# Remove opt-viewer, since this is just a compatibility package.
rm -Rf %{build_install_prefix}/share/opt-viewer

%endif


%check
# TODO: Fix test failures on arm
# FIXME: use %%cmake_build instead of %%__ninja
LD_LIBRARY_PATH=%{buildroot}/%{_libdir}  %{__ninja} check-all -C _build || \
%ifarch %{arm} %loongarch64
  :
%else
  false
%endif

%ldconfig_scriptlets libs

%if %{without compat_build}

%post devel
%{_sbindir}/update-alternatives --install %{_bindir}/llvm-config llvm-config %{_bindir}/llvm-config-%{__isa_bits} %{__isa_bits}

%postun devel
if [ $1 -eq 0 ]; then
  %{_sbindir}/update-alternatives --remove llvm-config %{_bindir}/llvm-config-%{__isa_bits}
fi

%endif

%files
%exclude %{_mandir}/man1/llvm-config*
%{_mandir}/man1/*
%{_bindir}/*

%if %{without compat_build}
%exclude %{_bindir}/llvm-config
%exclude %{_bindir}/llvm-config-%{__isa_bits}
%exclude %{_bindir}/not
%exclude %{_bindir}/count
%exclude %{_bindir}/yaml-bench
%exclude %{_bindir}/lli-child-target
%exclude %{_bindir}/llvm-isel-fuzzer
%exclude %{_bindir}/llvm-opt-fuzzer
%{_datadir}/opt-viewer
%else
%exclude %{pkg_bindir}/llvm-config
%{pkg_bindir}
%endif

%files libs
%{pkg_libdir}/libLLVM-%{maj_ver}.so
%if %{without compat_build}
%if %{with gold}
%{_libdir}/LLVMgold.so
%{_libdir}/bfd-plugins/LLVMgold.so
%endif
%{_libdir}/libLLVM-%{maj_ver}.%{min_ver}*.so
%{_libdir}/libLTO.so*
%else
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf
%if %{with gold}
%{_libdir}/%{name}/lib/LLVMgold.so
%endif
%{pkg_libdir}/libLLVM-%{maj_ver}.%{min_ver}*.so
%{pkg_libdir}/libLTO.so*
%exclude %{pkg_libdir}/libLTO.so
%endif
%{pkg_libdir}/libRemarks.so*

%files devel
%if %{without compat_build}
%ghost %{_bindir}/llvm-config
%{_bindir}/llvm-config-%{__isa_bits}
%{_mandir}/man1/llvm-config*
%{_includedir}/llvm
%{_includedir}/llvm-c
%{_libdir}/libLLVM.so
%{_libdir}/cmake/llvm
%exclude %{_libdir}/cmake/llvm/LLVMStaticExports.cmake
%exclude %{_libdir}/cmake/llvm/LLVMTestExports.cmake
%else
%{_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
%{pkg_bindir}/llvm-config
%{_mandir}/man1/llvm-config%{exec_suffix}.1.gz
%{install_includedir}/llvm
%{install_includedir}/llvm-c
%{pkg_includedir}/llvm
%{pkg_includedir}/llvm-c
%{pkg_libdir}/libLTO.so
%{pkg_libdir}/libLLVM.so
%{pkg_libdir}/cmake/llvm
%endif

%files doc
%doc %{_pkgdocdir}/html

%files static
%if %{without compat_build}
%{_libdir}/*.a
%exclude %{_libdir}/libLLVMTestingSupport.a
%{_libdir}/cmake/llvm/LLVMStaticExports.cmake
%else
%{_libdir}/%{name}/lib/*.a
%endif

%if %{without compat_build}

%files test
%{_libexecdir}/tests/llvm/
%{llvm_libdir}/unittests/
%{_datadir}/llvm/src/unittests
%{_datadir}/llvm/src/test.tar.gz
%{_datadir}/llvm/src/%{_arch}.site.cfg.py
%{_datadir}/llvm/src/%{_arch}.Unit.site.cfg.py
%{_datadir}/llvm/lit.fedora.cfg.py
%{_datadir}/llvm/src/docs/CommandGuide/dsymutil.rst
%{_bindir}/not
%{_bindir}/count
%{_bindir}/yaml-bench
%{_bindir}/lli-child-target
%{_bindir}/llvm-isel-fuzzer
%{_bindir}/llvm-opt-fuzzer
%{_libdir}/BugpointPasses.so
%{_libdir}/LLVMHello.so
%{_libdir}/cmake/llvm/LLVMTestExports.cmake

%files googletest
%{_datadir}/llvm/src/utils
%{_libdir}/libLLVMTestingSupport.a

%endif

%changelog
* Fri Mar 25 2022 l@raywang.cc - 11.0.0-3
- 11.0.0-3 loongarch64

* Thu Oct 29 2020 sguelton@redhat.com - 11.0.0-2
- Remove obsolete patch

* Wed Sep 30 2020 sguelton@redhat.com - 11.0.0-1
- 11.0.1 final release

* Wed Sep 30 2020 sguelton@redhat.com - 11.0.0-0.6.rc2
- Restore default CI behavior wrt. number of threads

* Fri Sep 25 2020 sguelton@redhat.com - 11.0.0-0.5.rc2
- Fix test case depending on fs capability

* Fri Sep 25 2020 sguelton@redhat.com - 11.0.0-0.4.rc2
- Fix dependency on dsymutil.rst from CI

* Thu Sep 24 2020 sguelton@redhat.com - 11.0.0-0.3.rc2
- Fix test file generation

* Wed Sep 23 2020 sguelton@redhat.com - 11.0.0-0.2.rc2
- Remove runtime dep on libedit-devel

* Mon Sep 14 2020 sguelton@redhat.com - 11.0.0-0.1.rc2
- 11.0.1.rc2 Release

* Wed Aug 19 2020 Tom Stellard <tstellar@redhat.com> - 10.0.1-3
- Fix rust crash on ppc64le compiling firefox

* Fri Jul 31 2020 sguelton@redhat.com - 10.0.1-2
- Fix llvm-config alternative handling, see rhbz#1859996

* Fri Jul 24 2020 sguelton@redhat.com - 10.0.1-1
- 10.0.1 Release

* Wed Jun 24 2020 sguelton@redhat.com - 10.0.0-2
- Reproducible build of test.tar.gz, see rhbz#1820319

* Tue Apr 7 2020 sguelton@redhat.com - 10.0.0-1
- 10.0.0 Release

* Thu Feb 27 2020 Josh Stone <jistone@redhat.com> - 9.0.1-4
- Fix a codegen bug for Rust

* Fri Jan 17 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-3
- Add explicit Requires from sub-packages to llvm-libs

* Fri Jan 10 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-2
- Fix crash with kernel bpf self-tests

* Thu Dec 19 2019 tstellar@redhat.com - 9.0.1-1
- 9.0.1 Release

* Wed Oct 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-5
- Remove work-around for threading issue in gold

* Wed Oct 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-4
- Build libLLVM.so first to avoid OOM errors

* Tue Oct 01 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-3
- Adjust run-lit-tests script to better match in tree testing

* Mon Sep 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-2
- Limit number of build threads using -l option for ninja

* Thu Sep 26 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-1
- 9.0.0 Release

* Thu Aug 1 2019 sguelton@redhat.com - 8.0.1-1
- 8.0.1 release

* Tue Jul 2 2019 sguelton@redhat.com - 8.0.1-0.3.rc2
- Deactivate multithreading for gold plugin only to fix rhbz#1636479

* Mon Jun 17 2019 sguelton@redhat.com - 8.0.1-0.2.rc2
- Deactivate multithreading instead of patching to fix rhbz#1636479

* Thu Jun 13 2019 sguelton@redhat.com - 8.0.1-0.1.rc2
- 8.0.1rc2 Release

* Tue May 14 2019 sguelton@redhat.com - 8.0.0-3
- Disable threading in LTO

* Wed May 8 2019 sguelton@redhat.com - 8.0.0-2
- Fix conflicts between llvm-static = 8 and llvm-dev < 8 around LLVMStaticExports.cmake

* Thu May 2 2019 sguelton@redhat.com - 8.0.0-1
- 8.0.0 Release

* Fri Dec 14 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-1
- 7.0.1 Release

* Thu Dec 13 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.5.rc3
- Drop compat libs

* Wed Dec 12 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.4.rc3
- Fix ambiguous python shebangs

* Tue Dec 11 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.3.rc3
- Disable threading in thinLTO

* Tue Dec 11 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.2.rc3
- Update cmake options for compat build

* Mon Dec 10 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.1.rc3
- 7.0.1-rc3 Release

* Fri Dec 07 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-14
- Don't build llvm-test on i686

* Thu Dec 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-13
- Fix build when python2 is not present on system

* Tue Nov 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-12
- Fix multi-lib installation of llvm-devel

* Tue Oct 23 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-11
- Add sub-packages for testing

* Mon Oct 01 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-10
- Drop scl macros

* Tue Aug 28 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-9
- Drop libedit dependency

* Tue Aug 14 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-8
- Only enabled valgrind functionality on arches that support it

* Mon Aug 13 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-7
- BuildRequires: python3-devel

* Mon Aug 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-6
- Backport fixes for rhbz#1610053, rhbz#1562196, rhbz#1595996

* Mon Aug 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-5
- Fix ld.so.conf.d path in files list

* Sat Aug 04 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-4
- Fix ld.so.conf.d path

* Fri Aug 03 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-3
- Install ld.so.conf so llvm libs are in the library search path

* Wed Jul 25 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-2
- Re-enable doc package now that BREW-2381 is fixed

* Tue Jul 10 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-1
- 6.0.1 Release

* Mon Jun 04 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-13
- Limit build jobs on ppc64 to avoid OOM errors

* Sat Jun 02 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-12
- Switch to python3-sphinx

* Thu May 31 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-11
- Remove conditionals to enable building only the llvm-libs package, we don't
  needs these for module builds.

* Wed May 23 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-10
- Add BuildRequires: libstdc++-static
- Resolves: #1580785

* Wed Apr 04 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-9
- Add conditionals to enable building only the llvm-libs package

* Tue Apr 03 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-8
- Drop BuildRequires: libstdc++-static this package does not exist in RHEL8

* Tue Mar 20 2018 Tilmann Scheller <tschelle@redhat.com> - 5.0.1-7
- Backport fix for rhbz#1558226 from trunk

* Tue Mar 06 2018 Tilmann Scheller <tschelle@redhat.com> - 5.0.1-6
- Backport fix for rhbz#1550469 from trunk

* Thu Feb 22 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-5
- Backport some retpoline fixes

* Tue Feb 06 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-4
- Backport retpoline support

* Mon Jan 29 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-3
- Backport r315279 to fix an issue with rust

* Mon Jan 15 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-2
- Drop ExculdeArch: ppc64

* Mon Jan 08 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-1
- 5.0.1 Release

* Thu Jun 22 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-3
- Fix Requires for devel package again.

* Thu Jun 22 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-2
- Fix Requires for llvm-devel

* Tue Jun 20 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- 4.0.1 Release

* Mon Jun 05 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-5
- Build for llvm-toolset-7 rename

* Mon May 01 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-4
- Remove multi-lib workarounds

* Fri Apr 28 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Fix build with llvm-toolset-4 scl

* Mon Apr 03 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Simplify spec with rpm macros.

* Thu Mar 23 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- LLVM 4.0.0 Final Release

* Wed Mar 22 2017 tstellar@redhat.com - 3.9.1-6
- Fix %%postun sep for -devel package.

* Mon Mar 13 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-5
- Disable failing tests on ARM.

* Sun Mar 12 2017 Peter Robinson <pbrobinson@fedoraproject.org> 3.9.1-4
- Fix missing mask on relocation for aarch64 (rhbz 1429050)

* Wed Mar 01 2017 Dave Airlie <airlied@redhat.com> - 3.9.1-3
- revert upstream radeonsi breaking change.

* Thu Feb 23 2017 Josh Stone <jistone@redhat.com> - 3.9.1-2
- disable sphinx warnings-as-errors

* Fri Feb 10 2017 Orion Poplawski <orion@cora.nwra.com> - 3.9.1-1
- llvm 3.9.1

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Nov 29 2016 Josh Stone <jistone@redhat.com> - 3.9.0-7
- Apply backports from rust-lang/llvm#55, #57

* Tue Nov 01 2016 Dave Airlie <airlied@gmail.com - 3.9.0-6
- rebuild for new arches

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-5
- apply the patch from -4

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-4
- add fix for lldb out-of-tree build

* Mon Oct 17 2016 Josh Stone <jistone@redhat.com> - 3.9.0-3
- Apply backports from rust-lang/llvm#47, #48, #53, #54

* Sat Oct 15 2016 Josh Stone <jistone@redhat.com> - 3.9.0-2
- Apply an InstCombine backport via rust-lang/llvm#51

* Wed Sep 07 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- llvm 3.9.0
- upstream moved where cmake files are packaged.
- upstream dropped CppBackend

* Wed Jul 13 2016 Adam Jackson <ajax@redhat.com> - 3.8.1-1
- llvm 3.8.1
- Add mips target
- Fix some shared library mispackaging

* Tue Jun 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 3.8.0-2
- fix color support detection on terminal

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- llvm 3.8.0 release

* Wed Mar 09 2016 Dan Horák <dan[at][danny.cz> 3.8.0-0.3
- install back memory consumption workaround for s390

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- llvm 3.8.0 rc3 release

* Fri Feb 19 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.1
- llvm 3.8.0 rc2 release

* Tue Feb 16 2016 Dan Horák <dan[at][danny.cz> 3.7.1-7
- recognize s390 as SystemZ when configuring build

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-6
- export C++ API for mesa.

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-5
- reintroduce llvm-static, clang needs it currently.

* Fri Feb 12 2016 Dave Airlie <airlied@redhat.com> 3.7.1-4
- jump back to single llvm library, the split libs aren't working very well.

* Fri Feb 05 2016 Dave Airlie <airlied@redhat.com> 3.7.1-3
- add missing obsoletes (#1303497)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.1-1
- new upstream release
- enable gold linker

* Wed Nov 04 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- fix Requires for subpackages on the main package

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
