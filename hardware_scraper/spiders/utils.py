def find_table(sections, table_name, css):
    try:
        return next(
            iter(
                section
                for section in sections
                if section.css(css).get().strip() == table_name
            )
        )
    except StopIteration:
        return None


def load_table_dict(loader, key_mapping, table_dict, full_name, logger):
    for key in key_mapping:
        dict_keys = key_mapping[key]
        if not isinstance(dict_keys, list):
            dict_keys = [dict_keys]

        dict_values = [table_dict.get(x) for x in dict_keys]
        dict_values = [x for x in dict_values if x is not None]
        if len(dict_values) == 1:
            loader.add_value(key, dict_values[0])
        elif len(dict_values) > 0:
            raise ValueError(
                f"Many keys are possible for key: {key}, dict_keys: {dict_keys}"
            )
        else:
            logger.info(f"No info on key: {key} on {full_name}")
