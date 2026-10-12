APP_NAME := INKAZA
ENTRYPOINT := launcher.pyw
ICON := assets/icon.png

DIST_DIR := dist
BUILD_DIR := build

.PHONY: clean build release

clean:
	rm -rf "$(DIST_DIR)" "$(BUILD_DIR)" "$(APP_NAME).spec"

build:
	pyinstaller \
		--noconfirm \
		--clean \
		--windowed \
		--onedir \
		--name "$(APP_NAME)" \
		--icon "$(ICON)" \
		--collect-all ttkbootstrap \
		--collect-all playwright \
		"$(ENTRYPOINT)"

release: clean build
	@echo "Build do $(APP_NAME) finalizado em $(DIST_DIR)/$(APP_NAME)."
