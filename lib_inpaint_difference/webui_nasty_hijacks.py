import functools
import gradio as gr

from modules import img2img

from lib_inpaint_difference.stack_ops import find_f_local_in_stack
from lib_inpaint_difference.ui import create_inpaint_difference_tab
from lib_inpaint_difference.globals import DifferenceGlobals


def hijack_img2img_processing():
    original_img2img_processing = img2img.img2img

    def hijack_func(id_task: str, mode: int, prompt: str, negative_prompt: str, prompt_styles, init_img, sketch,
            init_img_with_mask, inpaint_color_sketch, inpaint_color_sketch_orig, init_img_inpaint,
            init_mask_inpaint, steps: int, sampler_name: str, mask_blur: int, mask_alpha: float,
            inpainting_fill: int, n_iter: int, batch_size: int, cfg_scale: float, image_cfg_scale: float,
            denoising_strength: float, selected_scale_tab: int, height: int, width: int, scale_by: float,
            resize_mode: int, inpaint_full_res: bool, inpaint_full_res_padding: int,
            inpainting_mask_invert: int, img2img_batch_input_dir: str, img2img_batch_output_dir: str,
            img2img_batch_inpaint_mask_dir: str, override_settings_texts, img2img_batch_use_png_info: bool,
            img2img_batch_png_info_props: list, img2img_batch_png_info_dir: str, request: gr.Request, *args
    ):
        if mode == DifferenceGlobals.tab_index:
            mode = 2  # use the inpaint tab for processing
            init_img_with_mask = {
                'image': DifferenceGlobals.altered_image,
                'mask': DifferenceGlobals.generated_mask
            }

        return original_img2img_processing(id_task, mode, prompt, negative_prompt, prompt_styles, init_img, sketch,
            init_img_with_mask, inpaint_color_sketch, inpaint_color_sketch_orig, init_img_inpaint,
            init_mask_inpaint, steps, sampler_name, mask_blur, mask_alpha,
            inpainting_fill, n_iter, batch_size, cfg_scale, image_cfg_scale,
            denoising_strength, selected_scale_tab, height, width, scale_by,
            resize_mode, inpaint_full_res, inpaint_full_res_padding,
            inpainting_mask_invert, img2img_batch_input_dir, img2img_batch_output_dir,
            img2img_batch_inpaint_mask_dir, override_settings_texts, img2img_batch_use_png_info,
            img2img_batch_png_info_props, img2img_batch_png_info_dir, request, *args)

    img2img.img2img = hijack_func


def hijack_generation_params_ui():
    img2img_tabs = find_f_local_in_stack('img2img_tabs')
    for i, tab in enumerate(img2img_tabs):
        def hijack_select(*args, tab_index, original_select, **kwargs):
            fn = kwargs.get('fn')
            inputs = kwargs.get('inputs')
            outputs = kwargs.get('outputs')
            outputs.extend(DifferenceGlobals.ui_params)

            def hijack_select_img2img_tab(original_fn):
                nonlocal tab_index
                updates = list(original_fn())
                if tab_index == DifferenceGlobals.tab_index:
                    updates[0] = gr.update(visible=True)

                new_updates_state = gr.update(visible=tab_index == DifferenceGlobals.tab_index)
                new_updates = [new_updates_state] * len(DifferenceGlobals.ui_params)
                return *updates, *new_updates

            fn = functools.partial(hijack_select_img2img_tab, original_fn=fn)
            original_select(fn=fn, inputs=inputs, outputs=outputs)

        tab.select = functools.partial(hijack_select, tab_index=i, original_select=tab.select)


def hijack_gradio_tabs():
    def append_tabitem_to_img2img_tabs(tabitem):
        img2img_tabs = find_f_local_in_stack('img2img_tabs')
        img2img_selected_tab = find_f_local_in_stack('img2img_selected_tab')

        img2img_tabs.append(tabitem)
        DifferenceGlobals.tab_index = len(img2img_tabs)-1
        tabitem.select(fn=lambda tabnum=DifferenceGlobals.tab_index: tabnum, inputs=[], outputs=[img2img_selected_tab])

    original_gr_tabs = gr.Tabs

    class HijackedGrTabs(gr.Tabs):
        def __exit__(self, *args, **kwargs):
            if self.elem_id == "mode_img2img":
                tab_inpaint_difference = create_inpaint_difference_tab()
                DifferenceGlobals.img2img_tab = tab_inpaint_difference
                append_tabitem_to_img2img_tabs(tab_inpaint_difference)

            super().__exit__(*args, **kwargs)
            self.__class__ = original_gr_tabs

    gr.Tabs = HijackedGrTabs
