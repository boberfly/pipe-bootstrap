{

	"downloads" : [

		"https://github.com/janbar/openssl-cmake/archive/1.1.1b.tar.gz",

	],

	"license" : "LICENSE",

	"commands" : [

		"mkdir build",
		"cd build && "
			" cmake"
			" -G {cmakeGenerator}"
			" -D BUILD_OBJECT_LIBRARY_ONLY=ON"
			" -D CMAKE_BUILD_TYPE={cmakeBuildType}"
			" -D CMAKE_INSTALL_PREFIX={buildDir}"
			" ..",

		"cd build && cmake --build . --config {cmakeBuildType} --target install -- -j {jobs}",

	],

}
