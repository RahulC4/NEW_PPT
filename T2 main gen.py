mapped_templates = engine.map_templates(plan)
profile = engine.build_profile(plan, user_answers)
engine.generate_ppt(mapped_templates, profile)
