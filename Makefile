all: clean build

.PHONY: clean build

build:
		buildozer android debug deploy run
		adb logcat | grep python

clean:
		buildozer android clean 