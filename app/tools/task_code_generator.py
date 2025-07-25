import os
import yaml
import textwrap
from jinja2 import Template
from .code_utils import preserve_user_region

def generate_task_code(task_list, project_path):
    # base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    template_dir = os.path.join(project_root, "User_code", "task")
    output_dir = os.path.join(project_path, "User", "task")
    os.makedirs(output_dir, exist_ok=True)

    user_task_h_tpl = os.path.join(template_dir, "user_task.h.template")
    user_task_c_tpl = os.path.join(template_dir, "user_task.c.template")
    init_c_tpl = os.path.join(template_dir, "init.c.template")
    task_c_tpl = os.path.join(template_dir, "task.c.template")

    freq_tasks = [t for t in task_list if t.get("freq_control", True)]

    def render_template(path, context):
        with open(path, encoding="utf-8") as f:
            tpl = Template(f.read())
        return tpl.render(**context)

    context_h = {
        "thread_definitions": "\n".join([f"        osThreadId_t {t['name']};" for t in task_list]),
        "freq_definitions": "\n".join([f"        float {t['name']};" for t in freq_tasks]),
        "stack_definitions": "\n".join([f"        UBaseType_t {t['name']};" for t in task_list]),
        "last_up_time_definitions": "\n".join([f"        float {t['name']};" for t in freq_tasks]),
        "task_frequency_definitions": "\n".join([f"#define {t['name'].upper()}_FREQ ({t['frequency']})" for t in freq_tasks]),
        "task_init_delay_definitions": "\n".join([f"#define {t['name'].upper()}_INIT_DELAY ({t['delay']})" for t in task_list]),
        "task_attr_declarations": "\n".join([f"extern const osThreadAttr_t attr_{t['name']};" for t in task_list]),
        "task_function_declarations": "\n".join([f"void {t['function']}(void *argument);" for t in task_list]),
    }

    # ----------- 生成 user_task.h -----------
    user_task_h_path = os.path.join(output_dir, "user_task.h")
    new_user_task_h = render_template(user_task_h_tpl, context_h)

    if os.path.exists(user_task_h_path):
        with open(user_task_h_path, "r", encoding="utf-8") as f:
            old_code = f.read()
        for region in ["USER INCLUDE", "USER MESSAGE", "USER CONFIG"]:
            new_user_task_h = preserve_user_region(new_user_task_h, old_code, region)
    with open(user_task_h_path, "w", encoding="utf-8") as f:
        f.write(new_user_task_h)

    # ----------- 生成 user_task.c -----------
    context_c = {
        "task_attr_definitions": "\n".join([
            f"const osThreadAttr_t attr_{t['name']} = {{\n"
            f"    .name = \"{t['name']}\",\n"
            f"    .priority = osPriorityNormal,\n"
            f"    .stack_size = {t['stack']} * 4,\n"
            f"}};"
            for t in task_list
        ])
    }
    user_task_c = render_template(user_task_c_tpl, context_c)
    with open(os.path.join(output_dir, "user_task.c"), "w", encoding="utf-8") as f:
        f.write(user_task_c)

    # ----------- 生成 init.c -----------
    thread_creation_code = "\n".join([
        f"  task_runtime.thread.{t['name']} = osThreadNew({t['function']}, NULL, &attr_{t['name']});"
        for t in task_list
    ])
    context_init = {
        "thread_creation_code": thread_creation_code,
    }
    init_c = render_template(init_c_tpl, context_init)
    init_c_path = os.path.join(output_dir, "init.c")
    if os.path.exists(init_c_path):
        with open(init_c_path, "r", encoding="utf-8") as f:
            old_code = f.read()
        for region in ["USER INCLUDE", "USER CODE", "USER CODE INIT"]:
            init_c = preserve_user_region(init_c, old_code, region)
    with open(init_c_path, "w", encoding="utf-8") as f:
        f.write(init_c)

    # ----------- 生成 task.c -----------
    for t in task_list:
        desc = t.get("description", "")
        desc_wrapped = "\n    ".join(textwrap.wrap(desc, 20))
        context_task = {
            "task_name": t["name"],
            "task_function": t["function"],
            "task_frequency": f"{t['name'].upper()}_FREQ" if t.get("freq_control", True) else None,
            "task_delay": f"{t['name'].upper()}_INIT_DELAY",
            "task_description": desc_wrapped,
            "freq_control": t.get("freq_control", True)
        }
        with open(task_c_tpl, encoding="utf-8") as f:
            tpl = Template(f.read())
        code = tpl.render(**context_task)
        task_c_path = os.path.join(output_dir, f"{t['name']}.c")
        if os.path.exists(task_c_path):
            with open(task_c_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            for region in ["USER INCLUDE", "USER STRUCT", "USER CODE", "USER CODE INIT"]:
                code = preserve_user_region(code, old_code, region)
        with open(task_c_path, "w", encoding="utf-8") as f:
            f.write(code)

    # ----------- 保存任务配置到 config.yaml -----------
    config_yaml_path = os.path.join(output_dir, "config.yaml")
    with open(config_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(task_list, f, allow_unicode=True)