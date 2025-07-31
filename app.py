import os
import re
import json
import requests
import gradio as gr
from PIL import Image
import shutil
import tempfile

# 全局变量
api_base_url = "http://localhost:1234/v1"  # 默认API基础URL

def set_api_base_url(url):
    """设置API基础URL"""
    global api_base_url
    api_base_url = url.rstrip("/") + "/v1" if not url.endswith("/v1") else url
    return f"API基础URL已设置为: {api_base_url}"

def get_available_models(filter_vision=True):
    """从API获取可用模型，可选择筛选支持视觉的模型"""
    try:
        response = requests.get(f"{api_base_url}/models", timeout=10)
        if response.status_code == 200:
            models = response.json().get("data", [])
            
            # 如果需要筛选支持视觉的模型
            if filter_vision:
                vision_keywords = ["vision", "llava", "image", "clip", "blip", "img"]
                filtered_models = []
                for model in models:
                    model_id = model["id"].lower()
                    # 检查模型ID是否包含视觉相关关键字
                    if any(keyword in model_id for keyword in vision_keywords):
                        filtered_models.append(model)
                models = filtered_models
            
            return [model["id"] for model in models]
    except Exception as e:
        print(f"获取模型时出错: {e}")
    return []



def generate_caption_with_api(image_path, custom_prompt="", api_model=None):
    """使用API生成标题"""
    if not api_model:
        return "未选择API模型"
    
    try:
        # 准备请求数据
        with open(image_path, "rb") as img_file:
            import base64
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # 默认图像标题提示
        if not custom_prompt:
            custom_prompt = "详细描述这张图片"
        
        # 构建请求
        payload = {
            "model": api_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        # 发送请求到API
        response = requests.post(
            f"{api_base_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            caption = result["choices"][0]["message"]["content"]
            return caption.strip()
        else:
            return f"API请求失败: {response.status_code} - {response.text}"
    except Exception as e:
        return f"使用API生成标题时出错: {str(e)}"

def generate_caption(image, custom_prompt="", use_api=False, api_model=None):
    """为图像生成标题"""
    if image is None:
        return "未提供图像"
    
    # 将PIL图像保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        image.save(tmp_img.name, format="PNG")
        temp_image_path = tmp_img.name
    
    try:
        if use_api and api_model:
            # 使用API模型
            caption = generate_caption_with_api(temp_image_path, custom_prompt, api_model)
            return caption
        else:
            # 回退占位符
            if custom_prompt:
                return f"使用自定义提示生成的标题: {custom_prompt}"
            return "带有山脉和湖泊的美丽风景"
    finally:
        # 清理临时图像文件
        if os.path.exists(temp_image_path):
            os.unlink(temp_image_path)

def process_single_image(image, custom_prompt="", api_model=None):
    """处理单个图像进行测试"""
    if image is None:
        return "未上传图像"
    
    # 确定是否使用API
    use_api = api_model is not None
    
    caption = generate_caption(image, custom_prompt, use_api, api_model)
    return caption

def process_batch_images(input_dir, output_dir, custom_prompt="", api_model=None,
                        rename_images=False, prefix="", suffix="", start_number=1):
    """处理一批图像"""
    # 验证输入目录
    if not input_dir:
        return "请提供输入目录"
    
    if not os.path.exists(input_dir):
        return f"输入目录不存在: {input_dir}"
    
    # 验证输出目录
    if not output_dir:
        return "请提供输出目录"
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            return f"创建输出目录失败: {str(e)}"
    
    # 支持的图像扩展名
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
    
    # 获取所有图像文件
    try:
        image_files = [f for f in os.listdir(input_dir) 
                       if f.lower().endswith(image_extensions)]
    except Exception as e:
        return f"读取输入目录时出错: {str(e)}"
    
    if not image_files:
        return "在输入目录中未找到图像文件"
    
    # 排序文件以确保编号一致
    image_files.sort()
    
    # 确定是否使用API
    use_api = api_model is not None
    
    if not use_api:
        return "处理前请选择API模型"
    
    results = []
    for i, filename in enumerate(image_files):
        try:
            # 打开图像
            image_path = os.path.join(input_dir, filename)
            image = Image.open(image_path)
            
            # 生成标题
            caption = generate_caption(image, custom_prompt, use_api, api_model)
            
            # 如果重命名，确定新文件名
            if rename_images:
                number = start_number + i
                new_filename = f"{prefix}{number:04d}{suffix}"
                new_image_name = f"{new_filename}{os.path.splitext(filename)[1]}"
                new_caption_name = f"{new_filename}.txt"
            else:
                new_image_name = filename
                new_caption_name = f"{os.path.splitext(filename)[0]}.txt"
            
            # 将图像保存到输出目录
            output_image_path = os.path.join(output_dir, new_image_name)
            shutil.copy2(image_path, output_image_path)
            
            # 将标题保存到输出目录
            output_caption_path = os.path.join(output_dir, new_caption_name)
            with open(output_caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)
            
            results.append(f"已处理: {filename} -> {new_image_name} 并将标题保存为 {new_caption_name}")
        except Exception as e:
            results.append(f"处理 {filename} 时出错: {str(e)}")
    
    return "\n".join(results) if results else "未处理任何图像"

def update_model_list(filter_vision=True):
    """从API更新模型列表，可选择筛选支持视觉的模型"""
    models = get_available_models(filter_vision)
    return gr.Dropdown(choices=models, value=models[0] if models else None)

with gr.Blocks(title="图像批处理标记工具") as demo:
    gr.Markdown("# 图像批处理标记工具")
    
    # API 设置区域
    with gr.Group():
        gr.Markdown("## API 设置")
        with gr.Row():
            api_url_input = gr.Textbox(
                label="API 基础 URL",
                value="http://localhost:1234",
                placeholder="例如: http://localhost:1234 或 https://api.example.com"
            )
            set_api_url_btn = gr.Button("设置 API URL", variant="primary")
        
        with gr.Row():
            api_status = gr.Textbox(label="API 状态", interactive=False, scale=3)
        
        set_api_url_btn.click(
            fn=set_api_base_url,
            inputs=api_url_input,
            outputs=api_status
        )
    
    # 模型选择区域
    with gr.Group():
        gr.Markdown("## 模型选择")
        with gr.Row():
            api_model_dropdown = gr.Dropdown(
                choices=get_available_models(),
                label="选择 API 模型",
                value=None
            )
            filter_vision_checkbox = gr.Checkbox(
                label="仅显示支持视觉的模型",
                value=True
            )
            refresh_models_btn = gr.Button("刷新模型")
        
        refresh_models_btn.click(
            fn=update_model_list,
            inputs=filter_vision_checkbox,
            outputs=api_model_dropdown
        )
    
    # 主要功能区域
    with gr.Group():
        gr.Markdown("## 图像标记功能")
        
        with gr.Tab("单图像测试"):
            gr.Markdown("### 上传单张图像并生成标题")
            with gr.Row():
                with gr.Column(scale=1):
                    single_image_input = gr.Image(type="pil", label="上传图像")
                    single_process_btn = gr.Button("生成标题", variant="primary")
                with gr.Column(scale=1):
                    single_image_output = gr.Textbox(label="生成的标题", lines=5, max_lines=10)
            
            with gr.Row():
                single_custom_prompt = gr.Textbox(
                    label="自定义提示 (可选)",
                    placeholder="输入用于生成标题的自定义提示"
                )
                
            single_process_btn.click(
                fn=process_single_image,
                inputs=[single_image_input, single_custom_prompt, api_model_dropdown],
                outputs=single_image_output
            )
        
        with gr.Tab("批量处理"):
            gr.Markdown("### 批量处理图像目录")
            with gr.Row():
                input_dir = gr.Textbox(
                    label="输入目录",
                    placeholder="包含图像的目录路径"
                )
                output_dir = gr.Textbox(
                    label="输出目录",
                    placeholder="保存标记图像和标题文件的目录路径"
                )
            
            with gr.Row():
                custom_prompt = gr.Textbox(
                    label="自定义提示 (可选)",
                    placeholder="输入用于生成所有图像标题的自定义提示"
                )
            
            with gr.Accordion("重命名选项", open=False):
                with gr.Row():
                    rename_checkbox = gr.Checkbox(
                        label="重命名图像",
                        value=False
                    )
                with gr.Row():
                    prefix_input = gr.Textbox(
                        label="前缀",
                        value=""
                    )
                    suffix_input = gr.Textbox(
                        label="后缀",
                        value=""
                    )
                    start_number_input = gr.Number(
                        label="起始编号",
                        value=1,
                        precision=0
                    )
            
            with gr.Row():
                process_btn = gr.Button("开始批量处理", variant="primary")
                batch_output = gr.Textbox(label="处理结果", lines=5, max_lines=10)
            
            process_btn.click(
                fn=process_batch_images,
                inputs=[
                    input_dir, output_dir, custom_prompt, api_model_dropdown,
                    rename_checkbox, prefix_input, suffix_input, start_number_input
                ],
                outputs=batch_output
            )

if __name__ == "__main__":
    demo.launch()