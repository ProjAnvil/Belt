.PHONY: build build-all clean install test help

BINARY_NAME=belt
BUILD_DIR=bin
DIST_DIR=dist
MAIN_PATH=.

# Build for current platform
build:
	@echo "Building belt for current platform..."
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_PATH)
	@echo "✓ Built: $(BUILD_DIR)/$(BINARY_NAME)"

# Cross-compile for all platforms
build-all:
	@echo "Cross-compiling belt for all platforms..."
	@mkdir -p $(DIST_DIR)
	
	@echo "Building darwin/amd64..."
	GOOS=darwin GOARCH=amd64 go build -o $(DIST_DIR)/$(BINARY_NAME)-darwin-amd64 $(MAIN_PATH)
	
	@echo "Building darwin/arm64..."
	GOOS=darwin GOARCH=arm64 go build -o $(DIST_DIR)/$(BINARY_NAME)-darwin-arm64 $(MAIN_PATH)
	
	@echo "Building linux/amd64..."
	GOOS=linux GOARCH=amd64 go build -o $(DIST_DIR)/$(BINARY_NAME)-linux-amd64 $(MAIN_PATH)
	
	@echo "Building linux/arm64..."
	GOOS=linux GOARCH=arm64 go build -o $(DIST_DIR)/$(BINARY_NAME)-linux-arm64 $(MAIN_PATH)
	
	@echo "Building windows/amd64..."
	GOOS=windows GOARCH=amd64 go build -o $(DIST_DIR)/$(BINARY_NAME)-windows-amd64.exe $(MAIN_PATH)
	
	@echo "Building windows/arm64..."
	GOOS=windows GOARCH=arm64 go build -o $(DIST_DIR)/$(BINARY_NAME)-windows-arm64.exe $(MAIN_PATH)
	
	@echo "✓ All builds complete in $(DIST_DIR)/"
	@ls -lh $(DIST_DIR)/

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR)
	@echo "✓ Cleaned"

# Install to /usr/local/bin (requires sudo)
install: build
	@echo "Installing belt to /usr/local/bin..."
	@sudo cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/
	@echo "✓ Installed: /usr/local/bin/$(BINARY_NAME)"

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Show help
help:
	@echo "Belt CLI Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build       Build for current platform → bin/belt"
	@echo "  build-all   Cross-compile for darwin/linux/windows × amd64/arm64 → dist/"
	@echo "  clean       Remove bin/ and dist/"
	@echo "  install     Copy bin/belt to /usr/local/bin/ (requires sudo)"
	@echo "  test        Run Go tests"
	@echo "  help        Show this help message"
