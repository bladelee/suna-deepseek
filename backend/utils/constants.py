# Master model configuration - single source of truth
MODELS = {
    # Free tier models

    "anthropic/claude-sonnet-4-20250514": {
        "aliases": ["claude-sonnet-4"],
        "pricing": {
            "input_cost_per_million_tokens": 3.00,
            "output_cost_per_million_tokens": 15.00
        },
        "context_window": 200_000,  # 200k tokens
        "tier_availability": ["paid"]
    },
    "deepseek/deepseek-chat": {
        "aliases": ["deepseek-chat", "deepseek"],
        "pricing": {
            "input_cost_per_million_tokens": 0.38,
            "output_cost_per_million_tokens": 0.89
        },
        "context_window": 128_000,  # 128k tokens
        "tier_availability": ["free", "paid"]
    },
    "openrouter/deepseek/deepseek-chat": {
        "aliases": ["openrouter/deepseek-chat"],
        "pricing": {
            "input_cost_per_million_tokens": 0.38,
            "output_cost_per_million_tokens": 0.89
        },
        "context_window": 128_000,  # 128k tokens
        "tier_availability": ["free", "paid"]
    },
    # "openrouter/qwen/qwen3-235b-a22b": {
    #     "aliases": ["qwen3"],
    #     "pricing": {
    #         "input_cost_per_million_tokens": 0.13,
    #         "output_cost_per_million_tokens": 0.60
    #     },
    #     "tier_availability": ["free", "paid"]
    # },
    # "openrouter/google/gemini-2.5-flash-preview-05-20": {
    #     "aliases": ["gemini-flash-2.5"],
    #     "pricing": {
    #         "input_cost_per_million_tokens": 0.15,
    #         "output_cost_per_million_tokens": 0.60
    #     },
    #     "tier_availability": ["free", "paid"]
    # },
    "openrouter/deepseek/deepseek-chat-v3-0324": {
        "aliases": ["deepseek/deepseek-chat-v3-0324"],
        "pricing": {
            "input_cost_per_million_tokens": 0.38,
            "output_cost_per_million_tokens": 0.89
        },
        "context_window": 128_000,  # 128k tokens
        "tier_availability": ["free", "paid"]
    },
    "openrouter/moonshotai/kimi-k2": {
        "aliases": ["moonshotai/kimi-k2"],
        "pricing": {
            "input_cost_per_million_tokens": 1.00,
            "output_cost_per_million_tokens": 3.00
        },
        "context_window": 200_000,  # 200k tokens
        "tier_availability": ["paid"]
    },
    "xai/grok-4": {
        "aliases": ["grok-4", "x-ai/grok-4"],
        "pricing": {
            "input_cost_per_million_tokens": 5.00,
            "output_cost_per_million_tokens": 15.00
        },
        "context_window": 128_000,  # 128k tokens
        "tier_availability": ["paid"]
    },
    
    # Paid tier only models
    "gemini/gemini-2.5-pro": {
        "aliases": ["google/gemini-2.5-pro"],
        "pricing": {
            "input_cost_per_million_tokens": 1.25,
            "output_cost_per_million_tokens": 10.00
        },
        "context_window": 2_000_000,  # 2M tokens
        "tier_availability": ["paid"]
    },
    # "openai/gpt-4o": {
    #     "aliases": ["gpt-4o"],
    #     "pricing": {
    #         "input_cost_per_million_tokens": 2.50,
    #         "output_cost_per_million_tokens": 10.00
    #     },
    #     "tier_availability": ["paid"]
    # },
    # "openai/gpt-4.1": {
    #     "aliases": ["gpt-4.1"],
    #     "pricing": {
    #         "input_cost_per_million_tokens": 15.00,
    #         "output_cost_per_million_tokens": 60.00
    #     },
    #     "tier_availability": ["paid"]
    # },
    "openai/gpt-5": {
        "aliases": ["gpt-5"],
        "pricing": {
            "input_cost_per_million_tokens": 1.25,
            "output_cost_per_million_tokens": 10.00
        },
        "context_window": 400_000,  # 400k tokens
        "tier_availability": ["paid"]
    },
    "openai/gpt-5-mini": {
        "aliases": ["gpt-5-mini"],
        "pricing": {
            "input_cost_per_million_tokens": 0.25,
            "output_cost_per_million_tokens": 2.00
        },
        "context_window": 400_000,  # 400k tokens
        "tier_availability": ["free", "paid"]
    },
    # "openai/gpt-4.1-mini": {
    #     "aliases": ["gpt-4.1-mini"],
    #     "pricing": {
    #         "input_cost_per_million_tokens": 1.50,
    #         "output_cost_per_million_tokens": 6.00
    #     },
    #     "tier_availability": ["paid"]
    # },
    "anthropic/claude-3-7-sonnet-latest": {
        "aliases": ["sonnet-3.7"],
        "pricing": {
            "input_cost_per_million_tokens": 3.00,
            "output_cost_per_million_tokens": 15.00
        },
        "context_window": 200_000,  # 200k tokens
        "tier_availability": ["paid"]
    },
    "anthropic/claude-3-5-sonnet-latest": {
        "aliases": ["sonnet-3.5"],
        "pricing": {
            "input_cost_per_million_tokens": 3.00,
            "output_cost_per_million_tokens": 15.00
        },
        "context_window": 200_000,  # 200k tokens
        "tier_availability": ["paid"]
    },   
}

# Derived structures (auto-generated from MODELS)
def _generate_model_structures():
    """Generate all model structures from the master MODELS dictionary."""
    
    # Generate tier lists
    free_models = []
    paid_models = []
    
    # Generate aliases
    aliases = {}
    
    # Generate pricing
    pricing = {}
    
    # Generate context window limits
    context_windows = {}
    
    for model_name, config in MODELS.items():
        # Add to tier lists
        if "free" in config["tier_availability"]:
            free_models.append(model_name)
        if "paid" in config["tier_availability"]:
            paid_models.append(model_name)
        
        # Add aliases
        for alias in config["aliases"]:
            aliases[alias] = model_name
        
        # Add pricing
        pricing[model_name] = config["pricing"]
        
        # Add context window limits
        if "context_window" in config:
            context_windows[model_name] = config["context_window"]
        
        # Also add pricing and context windows for legacy model name variations
        if model_name.startswith("openrouter/deepseek/"):
            legacy_name = model_name.replace("openrouter/", "")
            pricing[legacy_name] = config["pricing"]
            if "context_window" in config:
                context_windows[legacy_name] = config["context_window"]
        elif model_name.startswith("openrouter/qwen/"):
            legacy_name = model_name.replace("openrouter/", "")
            pricing[legacy_name] = config["pricing"]
            if "context_window" in config:
                context_windows[legacy_name] = config["context_window"]
        elif model_name.startswith("gemini/"):
            legacy_name = model_name.replace("gemini/", "")
            pricing[legacy_name] = config["pricing"]
            if "context_window" in config:
                context_windows[legacy_name] = config["context_window"]
        elif model_name.startswith("anthropic/"):
            # Add anthropic/claude-sonnet-4 alias for claude-sonnet-4-20250514
            if "claude-sonnet-4-20250514" in model_name:
                pricing["anthropic/claude-sonnet-4"] = config["pricing"]
                if "context_window" in config:
                    context_windows["anthropic/claude-sonnet-4"] = config["context_window"]
        elif model_name.startswith("xai/"):
            # Add pricing for OpenRouter x-ai models
            openrouter_name = model_name.replace("xai/", "openrouter/x-ai/")
            pricing[openrouter_name] = config["pricing"]
            if "context_window" in config:
                context_windows[openrouter_name] = config["context_window"]
    
    return free_models, paid_models, aliases, pricing, context_windows

# Generate all structures
FREE_TIER_MODELS, PAID_TIER_MODELS, MODEL_NAME_ALIASES, HARDCODED_MODEL_PRICES, MODEL_CONTEXT_WINDOWS = _generate_model_structures()

MODEL_ACCESS_TIERS = {
    "free": FREE_TIER_MODELS,
    "tier_2_20": PAID_TIER_MODELS,
    "tier_6_50": PAID_TIER_MODELS,
    "tier_12_100": PAID_TIER_MODELS,
    "tier_25_200": PAID_TIER_MODELS,
    "tier_50_400": PAID_TIER_MODELS,
    "tier_125_800": PAID_TIER_MODELS,
    "tier_200_1000": PAID_TIER_MODELS,
    "tier_25_170_yearly_commitment": PAID_TIER_MODELS,
    "tier_6_42_yearly_commitment": PAID_TIER_MODELS,
    "tier_12_84_yearly_commitment": PAID_TIER_MODELS,
}

def get_model_context_window(model_name: str, default: int = 31_000) -> int:
    """
    Get the context window size for a given model.
    
    Args:
        model_name: The model name or alias
        default: Default context window if model not found
        
    Returns:
        Context window size in tokens
    """
    # Check direct model name first
    if model_name in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model_name]
    
    # Check if it's an alias
    if model_name in MODEL_NAME_ALIASES:
        canonical_name = MODEL_NAME_ALIASES[model_name]
        if canonical_name in MODEL_CONTEXT_WINDOWS:
            return MODEL_CONTEXT_WINDOWS[canonical_name]
    
    # Fallback patterns for common model naming variations
    if 'sonnet' in model_name.lower():
        return 200_000  # Claude Sonnet models
    elif 'gpt-5' in model_name.lower():
        return 400_000  # GPT-5 models
    elif 'gemini' in model_name.lower():
        return 2_000_000  # Gemini models
    elif 'grok' in model_name.lower():
        return 128_000  # Grok models
    elif 'gpt' in model_name.lower():
        return 128_000  # GPT-4 and variants
    elif 'deepseek' in model_name.lower():
        return 128_000  # DeepSeek models
    
    return default
