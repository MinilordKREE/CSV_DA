IMAGE   ?= csv_da_sandbox
DOCKERFILE := src/analysis/sandbox/docker/Dockerfile   
docker:    
	@command -v docker >/dev/null 2>&1 || { echo >&2 "❌ Docker is not installed. Please install it first."; exit 1; }
	docker build -f $(DOCKERFILE) -t $(IMAGE) $$(dirname $(DOCKERFILE))

clean:
	-docker rmi $(IMAGE)

.PHONY: docker clean help
