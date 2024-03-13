.PHONY: help build
.DEFAULT_GOAL := help


define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

build_lfactory: ## build docker container for llama factory
	docker build -t llamafactory -f ./lf_dockerfile .


run_lfactory: ## Run llama factory
	docker run -it --gpus device=0 \
				   -p 7860:7860\
				   -v /data2:/data2 \
				   -v /data:/data \
				   -v /home/msalvaris/repos/llm_finetuning:/workspace \
				   -v /home/msalvaris/.cache/:/root/.cache/ \
				   --shm-size=36gb \
				   llamafactory \
				   /bin/bash

run_grobid: ## Run grobid
	docker run --rm --gpus device=1 --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0


fine_tune: ## Finetune model, to be run inside llama-factory docker
	CUDA_VISIBLE_DEVICES=0 python /app/LLaMA-Factory/src/train_bash.py \
		--stage sft \
		--do_train \
		--model_name_or_path mistralai/Mistral-7B-Instruct-v0.2 \
		--dataset galore_qa \
		--dataset_dir /workspace/.data \
		--template default \
		--finetuning_type lora \
		--lora_target q_proj,v_proj,k_proj,o_proj,gate_proj,up_proj,down_proj \
		--lora_rank 32 \
		--lora_dropout 0.05 \
		--output_dir /workspace/.checkpoints/mistral_qa \
		--overwrite_cache \
    	--overwrite_output_dir \
		--per_device_train_batch_size 1 \
		--per_device_eval_batch_size 1 \
    	--gradient_accumulation_steps 8 \
		--lr_scheduler_type cosine \
		--logging_steps 10 \
		--save_steps 100 \
		--eval_steps 100 \
		--evaluation_strategy steps \
		--load_best_model_at_end \
		--learning_rate 5e-5 \
		--num_train_epochs 6.0 \
		--max_samples 3000 \
		--val_size 0.1 \
		--plot_loss \
		--fp16


cli: ## cli, to be run inside llama-factory docker
	CUDA_VISIBLE_DEVICES=0 python /app/LLaMA-Factory/src/cli_demo.py \
		--model_name_or_path mistralai/Mistral-7B-Instruct-v0.2 \
		--template default \
		--adapter_name_or_path /workspace/.checkpoints/mistral_qa \
    	--finetuning_type lora

api: ## start web end point
	API_PORT=7860 python /app/LLaMA-Factory/src/api_demo.py --model_name_or_path mistralai/Mistral-7B-Instruct-v0.2  --template default
