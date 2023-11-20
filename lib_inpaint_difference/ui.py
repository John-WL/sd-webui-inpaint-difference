import uuid

import gradio as gr
from modules.shared import opts
from modules.ui_components import ToolButton, FormRow

from lib_inpaint_difference.globals import DifferenceGlobals
from lib_inpaint_difference.mask_processing import compute_mask


class InpaintDifferenceTab:
    def __init__(self, tab_index: int):
        DifferenceGlobals.tab_index = tab_index

        self.inpaint_img_component = None
        self.inpaint_alt_component = None
        self.inpaint_mask_component = None
        self.swap_images = None

        self.mask_blur = None
        self.mask_dilation = None
        self.inpainting_mask_invert = None
        self.inpainting_fill = None
        self.inpaint_full_res = None
        self.inpaint_full_res_padding = None

    def tab(self):
        with gr.TabItem(label='Inpaint difference') as self.tab:
            with gr.Row():
                self.inpaint_img_component = gr.Image(label="Base image", source="upload", interactive=True, type="pil", elem_id="img_inpaint_difference")
                self.swap_images = ToolButton(value='⇆', elem_id=f'img2img_inpaint_difference_swap_images_{uuid.uuid4()}', elem_classes=['img2img_inpaint_difference_swap_images'], tooltip="Swap images.")
                self.inpaint_alt_component = gr.Image(label="Altered image", source="upload", interactive=True, type="pil", elem_id="alt_inpaint_difference")
            
            mask_component_height = getattr(opts, 'img2img_editor_height', 512)  # 512 is for SD.Next
            self.inpaint_mask_component = gr.Image(label="Difference mask", interactive=False, type="pil", elem_id="mask_inpaint_difference", height=mask_component_height)

    def section(self):
        with gr.Group():
            with FormRow():
                self.mask_blur = gr.Slider(label='Mask blur', minimum=0, maximum=64, step=1, value=4, elem_id="inpaint_difference_mask_blur")
                self.mask_dilation = gr.Slider(label='Mask dilation', maximum=100, step=1, value=0, elem_id='inpaint_difference_mask_dilation')

            with FormRow():
                self.inpainting_mask_invert = gr.Radio(label='Mask mode', choices=['Inpaint masked', 'Inpaint not masked'], value='Inpaint masked', type="index", elem_id="inpaint_difference_mask_mode")

            with FormRow():
                self.inpainting_fill = gr.Radio(label='Masked content', choices=['fill', 'original', 'latent noise', 'latent nothing'], value='original', type="index", elem_id="inpaint_difference_inpainting_fill")

            with FormRow():
                with gr.Column():
                    self.inpaint_full_res = gr.Radio(label="Inpaint area", choices=["Whole picture", "Only masked"], type="index", value="Whole picture", elem_id="inpaint_difference_inpaint_full_res")

                with gr.Column(scale=4):
                    self.inpaint_full_res_padding = gr.Slider(label='Only masked padding, pixels', minimum=0, maximum=256, step=4, value=32, elem_id="inpaint_difference_inpaint_full_res_padding")

    def gradio_events(self):
        compute_mask_dict = {
            'fn': compute_mask,
            'inputs': [
                self.inpaint_img_component,
                self.inpaint_alt_component,
                self.mask_blur,
                self.mask_dilation,
            ],
            'outputs': [
                self.inpaint_mask_component
            ]
        }

        self.inpaint_img_component.upload(**compute_mask_dict)
        self.inpaint_img_component.clear(**compute_mask_dict)
        self.inpaint_alt_component.upload(**compute_mask_dict)
        self.inpaint_alt_component.clear(**compute_mask_dict)
        self.mask_blur.release(**compute_mask_dict)
        self.mask_dilation.release(**compute_mask_dict)

        def swap_images_func(img, alt, blur_amount, dilation_amount):
            visual_mask = compute_mask(alt, img, blur_amount, dilation_amount)
            DifferenceGlobals.base_image = alt
            DifferenceGlobals.altered_image = img
            return gr.update(value=alt), gr.update(value=img), gr.update(value=visual_mask)

        self.swap_images.click(
            fn=swap_images_func,
            inputs=compute_mask_dict['inputs'],
            outputs=[
                self.inpaint_img_component,
                self.inpaint_alt_component,
                self.inpaint_mask_component,
            ]
        )

        def update_ui_params_globals(mask_blur, mask_dilation, inpainting_mask_invert, inpainting_fill, inpaint_full_res, inpaint_full_res_padding):
            DifferenceGlobals.mask_blur = mask_blur
            DifferenceGlobals.mask_dilation = mask_dilation
            DifferenceGlobals.inpainting_mask_invert = inpainting_mask_invert
            DifferenceGlobals.inpainting_fill = inpainting_fill
            DifferenceGlobals.inpaint_full_res = inpaint_full_res
            DifferenceGlobals.inpaint_full_res_padding = inpaint_full_res_padding

        update_custom_ui_globals_dict = {
            'fn': update_ui_params_globals,
            'inputs': [
                self.mask_blur,
                self.mask_dilation,
                self.inpainting_mask_invert,
                self.inpainting_fill,
                self.inpaint_full_res,
                self.inpaint_full_res_padding
            ],
            'outputs': []
        }

        self.tab.select(**update_custom_ui_globals_dict)
        self.mask_blur.release(**update_custom_ui_globals_dict)
        self.mask_dilation.release(**update_custom_ui_globals_dict)
        self.inpainting_mask_invert.change(**update_custom_ui_globals_dict)
        self.inpainting_fill.change(**update_custom_ui_globals_dict)
        self.inpaint_full_res.change(**update_custom_ui_globals_dict)
        self.inpaint_full_res_padding.release(**update_custom_ui_globals_dict)
