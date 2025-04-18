IMAGE   ?= csv_da_sandbox
DOCKERFILE := src/analysis/sandbox/docker/Dockerfile   
docker:    
	docker build -f $(DOCKERFILE) -t $(IMAGE) $$(dirname $(DOCKERFILE))

clean:
	-docker rmi $(IMAGE)

.PHONY: docker clean help
