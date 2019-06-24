{

	"downloads" : [

		"https://github.com/python-cmake-buildsystem/python-cmake-buildsystem/archive/master.tar.gz",
		"https://www.python.org/ftp/python/2.7.16/Python-2.7.16.tgz",

	],

	"commands" : [
		"cmake -E rename ../Python-2.7.16 ./Python-2.7.16",

		"cmake -E make_directory build",

		"cd build && cmake"
			" -Wno-dev"
			" -G {cmakeGenerator}"
			" -D CMAKE_BUILD_TYPE={cmakeBuildType}"
			" -D CMAKE_INSTALL_PREFIX={buildDir}"
			" -D PYTHON_VERSION=2.7.16"
			" -D DOWNLOAD_SOURCES=OFF"
			" -D BUILD_LIBPYTHON_SHARED=OFF"
			" -D BUILD_EXTENSIONS_AS_BUILTIN=ON"
			" -D Py_UNICODE_SIZE=4"
			" -D USE_LIB64=OFF"
			" -D INSTALL_TEST=OFF"
			" -D OPENSSL_INCLUDE_DIR={buildDir}/include"
			" -D OPENSSL_LIBRARIES={buildDir}/libcrypto.a {buildDir}/libssl.a"
			" ..",
		"cd build && cmake --build . --config {cmakeBuildType} --target install -- -j {jobs}",
		"cmake -E copy ./Python-2.7.16/LICENSE {buildDir}/doc/licenses/Python",

	],

}
