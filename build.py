#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
#  Modified by Alex Fuller for pipe-bootstrap building.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of Alex Fuller nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import sys
import distutils.util
import uuid
import json
import shutil
import argparse
import subprocess
import multiprocessing

# Set the platform.

platform = ""
if "linux" in sys.platform:
    platform = "linux"
elif "darwin" in sys.platform:
    platform = "osx"
elif "win32" in sys.platform:
    platform = "windows"

parser = argparse.ArgumentParser()

parser.add_argument(
	"--version",
	help = "The version to build. Can either be a tag or SHA1 commit hash."
)

parser.add_argument(
	"--upload",
	type = distutils.util.strtobool,
	default = "0",
	help = "Uploads the resulting package to the GitHub release page. You must "
	       "have manually created the release and release notes already."
)

parser.add_argument(
	"--docker",
	type = distutils.util.strtobool,
	default = "linux" in sys.platform,
	help = "Performs the build using a Docker container. This provides a "
	       "known build platform so that builds are repeatable."
)

parser.add_argument(
	"--interactive",
	type = distutils.util.strtobool,
	default = False,
	help = "When using docker, starts an interactive shell rather than "
		   "performing the build. This is useful for debugging."
)

parser.add_argument(
	"--platform",
	default = platform,
    choices = [ "linux", "osx", "windows" ],
	help = "The platform to build for. "
)

parser.add_argument(
	"--forceCCompiler",
	default = "gcc",
	help = "Force a particular C compiler."
)

parser.add_argument(
	"--forceCxxCompiler",
	default = "g++",
	help = "Force a particular C++ compiler."
)

parser.add_argument(
	"--output",
	default = "out",
	help = "The output directory."
)

args = parser.parse_args()

if args.interactive :
	if not args.docker :
		parser.exit( 1, "--interactive requires --docker\n" )
	if args.version or args.upload :
		parser.exit( 1, "--interactive can not be used with other flags\n" )
else :
	if not args.version :
		parser.exit( "--version argument is required")

# Check that our environment contains everything we need to do a build.

for envVar in ( "GITHUB_RELEASE_TOKEN", ) :
	if envVar not in os.environ	:
		parser.exit( 1,  "{0} environment variable not set".format( envVar ) )

# Build a little dictionary of variables we'll need over and over again
# in string formatting operations, and use it to figure out what
# package we will eventually be generating.

formatVariables = {
	"version" : args.version,
	"upload" : args.upload,
	"platform" : args.platform,
	"releaseToken" : os.environ["GITHUB_RELEASE_TOKEN"],
	"auth" : '-H "Authorization: token {}"'.format( os.environ["GITHUB_RELEASE_TOKEN"] ),
	"cmakeGenerator" : "\"Unix Makefiles\"",
	"cxx" : args.forceCxxCompiler,
	"c" : args.forceCCompiler,
	"output" : os.path.abspath( args.output ),
	"cmakeBuildType" : "Release",
}

# Output directory

if not os.path.isdir( formatVariables["output"] ) :
	os.makedirs( formatVariables["output"] )

packageName = "pipe-bootstrap-{version}-{platform}".format( **formatVariables )
formatVariables["uploadFile"] = "%s.tar.gz" % packageName

# If we're going to be doing an upload, then check that the release exists. Better
# to find out now than at the end of a lengthy build.

def releaseId() :

	release = subprocess.check_output(
		"curl -s {auth} https://api.github.com/repos/boberfly/pipe-bootstrap/releases/tags/{version}".format(
			**formatVariables
		),
		shell = True
	)
	release = json.loads( release )
	return release.get( "id" )

if args.upload and releaseId() is None :
	parser.exit( 1, "Release {version} not found\n".format( **formatVariables ) )

# Restart ourselves inside a Docker container so that we use a repeatable
# build environment.

if args.docker and not os.path.exists( "/.dockerenv" ) :

	imageCommand = "docker build -t pipe-boostrap-build .".format( **formatVariables )
	sys.stderr.write( imageCommand + "\n" )
	subprocess.check_call( imageCommand, shell = True )

	#containerMounts = "-v {output}:/out:rw,Z".format( **formatVariables )
	containerEnv = "GITHUB_RELEASE_TOKEN={releaseToken}".format( **formatVariables )
	containerName = "pipe-boostrap-build-{id}".format( id = uuid.uuid1() )

	if args.interactive :
		containerBashCommand = "{env} bash".format( env = containerEnv )
	else :
		containerBashCommand = "{env} ./build.py --version {version} --upload {upload} --platform {platform} --output=./out".format( env = containerEnv, **formatVariables )

	containerCommand = "docker run --name {name} -i -t pipe-boostrap-build -c '{command}'".format(
		name = containerName,
		#mounts = containerMounts,
		command = containerBashCommand
	)

	sys.stderr.write( containerCommand + "\n" )
	subprocess.check_call( containerCommand, shell = True )

	if not args.interactive :
		# Copy out the generated package.
		copyCommand = "docker cp {container}:/out/{uploadFile} {output}".format(
			container = containerName,
			**formatVariables
		)
		sys.stderr.write( copyCommand + "\n" )
		subprocess.check_call( copyCommand, shell = True )

	sys.exit( 0 )

# Perform the build.

pythonEnvs = "REZ_CONFIG_FILE=/tmp/myrezconfig.py PATH=/install/{platform}/bin:$PATH PYTHONHOME=/install/{platform} PYTHONPATH=/install/{platform}/lib/python2.7 LD_LIBRARY_PATH=/install/{platform}/lib".format( **formatVariables )

depCommands = [
	"curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py",
	"python get-pip.py",
	"pip install cmake",
	"git clone https://github.com/mottosso/rez-pipz.git",
	"cmake -E make_directory install/{platform}".format( **formatVariables ),

	"cd dependencies && "
	"./build/build.py --project Zlib --buildDir /install/{platform} --forceCCompiler {c} && "
	"./build/build.py --project OpenSSL --buildDir /install/{platform} --forceCCompiler {c} && "
	"./build/build.py --project Python --buildDir /install/{platform} --forceCCompiler {c}".format( **formatVariables ),
]

commands = [
	"cd /install/{platform}/bin && {env} ./python /get-pip.py".format( env=pythonEnvs, **formatVariables ),
	"cd /install/{platform}/bin && {env} ./pip install bleeding-rez --pre".format( env=pythonEnvs, **formatVariables ),
	"cd /install/{platform}/bin && /fix-shebang rez* pip _rez* bez easy_install wheel".format( **formatVariables ),
	"mv /run /install/{platform}/run && "
	"mkdir /install/{platform}/packages".format( **formatVariables ),

	"rm -f /install/{platform}/lib/python2.7/config/libpython2.7.a".format( **formatVariables ),
	"cd /install/{platform}/bin && mv python rezpy && "
	"rm -f python2.7 python2 && ln -s rezpy rezpy2 && ln -s rezpy rezpy2.7".format( **formatVariables ),

	"echo 'packages_path = [\"/install/{platform}/packages\"]' > /tmp/myrezconfig.py".format( **formatVariables ),
	"cd /install/{platform}/bin && "
	"{env} ./rez bind -i /install/{platform}/packages platform && "
	"{env} ./rez bind -i /install/{platform}/packages arch && "
	"{env} ./rez bind -i /install/{platform}/packages os".format( env=pythonEnvs, **formatVariables ),
	"mv /python /install/{platform}/packages/ && "
	"cd /install/{platform}/packages/python/2.7.16/platform-linux/arch-x86_64/bin && ln -s ../../../../../../bin/rezpy python && rm .keepme && "
	"cd /install/{platform}/packages/python/2.7.16/platform-linux/arch-x86_64/python && ln -s ../../../../../../lib/python2.7 lib && rm .keepme && "
	"cd /install/{platform}/packages/python/2.7.16/platform-linux/arch-x86_64/python && ln -s ../../../../../../lib/python2.7/site-packages extra && "
	"cd /rez-pipz && {env} PYTHONHTTPSVERIFY=0 /install/{platform}/bin/rez build --install -p /install/{platform}/packages".format( env=pythonEnvs, **formatVariables ),

	"cd /install/{platform} && "
	"rm -f bin/openssl && "
	"rm -rf ssl && rm -rf share && "
	"rm -f lib/libcrypto.a lib/libssl.a lib/libz.* lib/libpython2.7.a && "
	"rm -rf lib/engines lib/pkgconfig && "
	"rm -rf include".format( **formatVariables ),

	"cd /install/{platform} && "
	"tar -c -z -f /tmp/intermediate.tar * && "
	"rm -rf /tmp/{packageName} && "
	"mkdir /tmp/{packageName} && "
	"cd /tmp/{packageName} && "
	"tar -x -f /tmp/intermediate.tar && "
	"cd /tmp && "
	"tar -c -z -f {output}/{uploadFile} {packageName}".format( 
		packageName=packageName, **formatVariables ),
]

#env = os.environ.copy()
#env["LD_LIBRARY_PATH"] = gafferDirName + os.sep + "lib" + os.pathsep + env.get( "LD_LIBRARY_PATH", "" )

for command in depCommands :
	sys.stderr.write( command + "\n" )
	subprocess.check_call( command, shell = True )

for command in commands :
	sys.stderr.write( command + "\n" )
	subprocess.check_call( command, shell = True )

# Upload the build

if args.upload :

	uploadCommand = (
		'curl {auth}'
		' -H "Content-Type: application/zip"'
		' --data-binary @{uploadFile} "{uploadURL}"'
		' -o /tmp/curlResult.txt' # Must specify output file in order to get progress output
	).format(
		uploadURL = "https://uploads.github.com/repos/boberfly/pipe-bootstrap/releases/{id}/assets?name={uploadName}".format(
			id = releaseId(),
			uploadName = os.path.basename( formatVariables["uploadFile"] ),
			**formatVariables
		),
		**formatVariables
	)

	sys.stderr.write( "Uploading package\n" )
	sys.stderr.write( uploadCommand + "\n" )

	subprocess.check_call( uploadCommand, shell = True )