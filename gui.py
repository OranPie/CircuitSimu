#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Simulator GUI (Tkinter + Canvas)
- Modern graphical interface with canvas-based circuit editor
- Mouse-driven interaction
- Component palette and property editor
"""

import json
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, simpledialog
from typing import Any, Optional, Tuple, Dict, List
import math

from core import Circuit, Component, SolveResult, solve_circuit, comp_symbol, format_si, format_si_safe, format_value, bulb_resistance, Point, meter_ranges, meter_full_scale, meter_native_full_scale, CircuitHistory, goal_seek_parameter

SAVE_FILE = "circuit.json"
GRID_SIZE = 20
CANVAS_W = 1200
CANVAS_H = 600

I18N: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "Circuit Simulator - GUI",
        "component_palette": "Component Palette",
        "actions": "Actions",
        "inspector": "Inspector",
        "no_selection": "No selection",
        "range": "Range",
        "no_ranges": "No ranges configured",
        "closed": "Closed",
        "throw": "Throw",
        "momentary_button": "Momentary button",
        "press": "Press",
        "release": "Release",
        "solve": "🔄 Solve Circuit",
        "goal_seek": "🎯 Goal Seek",
        "wire_tool": "✏ Wire Tool",
        "navigate": "🧭 Navigate",
        "save": "💾 Save",
        "load": "📂 Load",
        "clear_all": "🗑️ Clear All",
        "mode_navigate": "Mode: Navigate",
        "mode_wire": "Mode: Wire",
        "mode_place": "Mode: Place {ctype}",
        "status_ready": "Ready",
        "status_navigate": "Navigate mode",
        "status_wire": "Wire tool: click start then end",
        "status_place": "Click on canvas to place {ctype}",
        "undo": "Undo",
        "redo": "Redo",
        "nothing_to_undo": "Nothing to undo",
        "nothing_to_redo": "Nothing to redo",
        "simulation_failed_singular": "Simulation failed: Singular matrix",
        "simulation_complete": "Simulation complete",
        "saved_to": "Saved to {path}",
        "loaded_from": "Loaded from {path}",
        "circuit_cleared": "Circuit cleared",
        "wire_start": "Wire start: {pos}. Click end point.",
        "wire_added": "Wire added: {a} -> {b}",
        "placed": "Placed {ctype} at {pos}",
        "deleted": "Deleted {name}",
        "switch_opened": "Switch opened",
        "switch_closed": "Switch closed",
        "warnings": "Warnings",
        "hover_hint": "Hover over or click a component to see details.",
        "left_click": "Left-click: Select",
        "right_click": "Right-click: Menu",
        "double_click": "Double-click: Edit",
        "info_component": "Component",
        "info_type": "Type",
        "info_endpoints": "Endpoints",
        "info_measurements": "Measurements",
        "info_voltage": "Voltage",
        "info_current": "Current",
        "info_power": "Power",
        "info_params": "Parameters",
        "info_status": "Status",
        "flag_open": "Open circuit",
        "flag_source_overcurrent": "Source overcurrent",
        "flag_overcurrent": "Overcurrent",
        "ol": "OL",
        "language": "Language",
        "lang_en": "English",
        "lang_zh": "中文",
        "comp_socket": "Socket",
        "comp_wire": "Wire",
        "comp_resistor": "Resistor",
        "comp_bulb": "Bulb",
        "comp_rheostat": "Rheostat",
        "comp_switch_spst": "Switch SPST",
        "comp_switch_spdt": "Switch SPDT",
        "comp_switch_sp3t": "Switch SP3T",
        "comp_switch_dpst": "Switch DPST",
        "comp_switch_dpdt": "Switch DPDT",
        "comp_button_momentary": "Button (momentary)",
        "comp_ammeter": "Ammeter",
        "comp_voltmeter": "Voltmeter",
        "comp_galvanometer": "Galvanometer",

        "clear_all_confirm_title": "Clear All",
        "clear_all_confirm_msg": "Delete all components?",
        "save_error": "Save Error",
        "load_error": "Load Error",
        "invalid_input": "Invalid Input",
        "ok": "OK",
        "cancel": "Cancel",

        "panel_selection": "Selection",
        "panel_measurements": "Measurements",
        "panel_status": "Status",
        "panel_shortcuts": "Shortcuts",
        "selected": "Selected",
        "hovered": "Hovered",
        "none": "None",
        "solve_ok": "OK",
        "solve_failed": "Failed",

        "edit_title": "Edit {name}",
        "edit_properties": "Edit Properties",
        "prop_voltage": "Voltage (V)",
        "prop_current_warning": "Current Warning (A)",
        "prop_resistance": "Resistance (Ω)",
        "prop_rated_voltage": "Rated Voltage (V)",
        "prop_rated_power": "Rated Power (W)",
        "prop_state": "State (1=closed, 0=open)",
        "prop_throw": "Throw",
        "prop_internal_resistance": "Internal Resistance (Ω)",
        "prop_coil_resistance": "Coil Resistance (Ω)",
        "prop_full_scale_current": "Full Scale Current (A)",

        "gs_dialog_title": "Goal Seek",
        "gs_dialog_header": "Goal Seek",
        "gs_variable_component": "Variable component",
        "gs_variable_prop": "Variable prop",
        "gs_measure": "Measure",
        "gs_measure_component": "Measure component",
        "gs_component": "Component",
        "gs_node": "Node",
        "gs_field": "Field",
        "gs_branch_optional": "Branch (optional)",
        "gs_abs_value": "abs(value)",
        "gs_node_xy": "Node x,y",
        "gs_abs": "abs",
        "gs_target": "Target",
        "gs_lo_hi": "Lo / Hi",
        "gs_reject_overcurrent": "Reject overcurrent",
        "gs_auto_range": "Auto-range meter for target",
        "gs_err_choose_var": "Please choose a variable component",
        "gs_err_target_lo_hi": "Target/Lo/Hi must be numbers",
        "gs_err_node_int": "Node x/y must be integers",
        "gs_err_choose_meas": "Please choose a measurement component",

        "menu_edit": "Edit Properties",
        "menu_delete": "Delete",
        "menu_duplicate": "Duplicate",
        "menu_lock": "Lock",
        "menu_unlock": "Unlock",
        "menu_toggle": "Toggle",
        "menu_cycle": "Cycle",

        "tab_inspector": "Inspector",
        "tab_options": "Options",
        "opt_format": "Number format",
        "opt_fmt_si": "SI",
        "opt_fmt_sci": "Scientific",
        "opt_sig": "Significant digits",
        "opt_max_abs": "Max abs (> marker)",
        "opt_min_abs": "Min abs (~0 marker)",
        "opt_show_shortcuts": "Show shortcuts card",
        "opt_show_labels": "Show value labels on canvas",
        "opt_defaults": "Defaults",
        "opt_def_source_v": "Source V",
        "opt_def_source_iwarn": "Source Iwarn",
        "opt_def_res_r": "Resistor R",
        "opt_def_rheo_r": "Rheostat R",
        "opt_def_rheo_min": "Rheostat Rmin",
        "opt_def_rheo_max": "Rheostat Rmax",
        "opt_def_amm_burden": "Ammeter burden_V",
        "opt_def_volt_sens": "Voltmeter ohm_per_V",
        "opt_def_gal_r": "Galv Rcoil",
        "opt_def_gal_ifs": "Galv Ifs",
        "apply": "Apply",
        "options": "⚙ Options",
        "locked": "Locked",
    },
    "zh": {
        "app_title": "电路模拟器 - GUI",
        "component_palette": "元件库",
        "actions": "操作",
        "inspector": "检查器",
        "no_selection": "未选择",
        "range": "量程",
        "no_ranges": "未配置量程",
        "closed": "闭合",
        "throw": "拨动",
        "momentary_button": "瞬时按钮",
        "press": "按下",
        "release": "松开",
        "solve": "🔄 求解",
        "goal_seek": "🎯 反求",
        "wire_tool": "✏ 布线",
        "navigate": "🧭 浏览",
        "save": "💾 保存",
        "load": "📂 载入",
        "clear_all": "🗑️ 清空",
        "mode_navigate": "模式：浏览",
        "mode_wire": "模式：布线",
        "mode_place": "模式：放置 {ctype}",
        "status_ready": "就绪",
        "status_navigate": "浏览模式",
        "status_wire": "布线：先点起点再点终点",
        "status_place": "点击画布放置 {ctype}",
        "undo": "撤销",
        "redo": "重做",
        "nothing_to_undo": "无可撤销",
        "nothing_to_redo": "无可重做",
        "simulation_failed_singular": "仿真失败：矩阵奇异",
        "simulation_complete": "仿真完成",
        "saved_to": "已保存到 {path}",
        "loaded_from": "已从 {path} 载入",
        "circuit_cleared": "已清空电路",
        "wire_start": "布线起点：{pos}，请点击终点",
        "wire_added": "已布线：{a} -> {b}",
        "placed": "已放置 {ctype} 于 {pos}",
        "deleted": "已删除 {name}",
        "switch_opened": "开关已断开",
        "switch_closed": "开关已闭合",
        "warnings": "告警",
        "hover_hint": "悬停或点击元件查看详情。",
        "left_click": "左键：选择",
        "right_click": "右键：菜单",
        "double_click": "双击：编辑",
        "info_component": "元件",
        "info_type": "类型",
        "info_endpoints": "端点",
        "info_measurements": "测量",
        "info_voltage": "电压",
        "info_current": "电流",
        "info_power": "功率",
        "info_params": "参数",
        "info_status": "状态",
        "flag_open": "断路",
        "flag_source_overcurrent": "电源过流",
        "flag_overcurrent": "过流",
        "ol": "OL",
        "language": "语言",
        "lang_en": "English",
        "lang_zh": "中文",
        "comp_socket": "电源",
        "comp_wire": "导线",
        "comp_resistor": "电阻",
        "comp_bulb": "灯泡",
        "comp_rheostat": "滑变",
        "comp_switch_spst": "开关SPST",
        "comp_switch_spdt": "开关SPDT",
        "comp_switch_sp3t": "开关SP3T",
        "comp_switch_dpst": "开关DPST",
        "comp_switch_dpdt": "开关DPDT",
        "comp_button_momentary": "按钮(瞬时)",
        "comp_ammeter": "电流表",
        "comp_voltmeter": "电压表",
        "comp_galvanometer": "检流计",

        "clear_all_confirm_title": "清空",
        "clear_all_confirm_msg": "删除所有元件？",
        "save_error": "保存错误",
        "load_error": "载入错误",
        "invalid_input": "输入无效",
        "ok": "确定",
        "cancel": "取消",

        "panel_selection": "元件",
        "panel_measurements": "测量",
        "panel_status": "状态",
        "panel_shortcuts": "快捷",
        "selected": "选中",
        "hovered": "悬停",
        "none": "无",
        "solve_ok": "正常",
        "solve_failed": "失败",

        "edit_title": "编辑 {name}",
        "edit_properties": "编辑参数",
        "prop_voltage": "电压 (V)",
        "prop_current_warning": "过流阈值 (A)",
        "prop_resistance": "电阻 (Ω)",
        "prop_rated_voltage": "额定电压 (V)",
        "prop_rated_power": "额定功率 (W)",
        "prop_state": "状态 (1=闭合, 0=断开)",
        "prop_throw": "拨动",
        "prop_internal_resistance": "内阻 (Ω)",
        "prop_coil_resistance": "线圈电阻 (Ω)",
        "prop_full_scale_current": "满偏电流 (A)",

        "gs_dialog_title": "反求",
        "gs_dialog_header": "反求 (Goal Seek)",
        "gs_variable_component": "变量元件",
        "gs_variable_prop": "变量属性",
        "gs_measure": "测量",
        "gs_measure_component": "测量元件",
        "gs_component": "元件",
        "gs_node": "节点",
        "gs_field": "字段",
        "gs_branch_optional": "支路(可选)",
        "gs_abs_value": "取绝对值",
        "gs_node_xy": "节点 x,y",
        "gs_abs": "abs",
        "gs_target": "目标",
        "gs_lo_hi": "下限 / 上限",
        "gs_reject_overcurrent": "拒绝过流(短路即无解)",
        "gs_auto_range": "测量表自动选档",
        "gs_err_choose_var": "请选择变量元件",
        "gs_err_target_lo_hi": "目标/上下限必须是数字",
        "gs_err_node_int": "节点 x/y 必须为整数",
        "gs_err_choose_meas": "请选择测量元件",

        "menu_edit": "编辑参数",
        "menu_delete": "删除",
        "menu_duplicate": "复制",
        "menu_lock": "锁定",
        "menu_unlock": "解锁",
        "menu_toggle": "切换",
        "menu_cycle": "循环切换",

        "tab_inspector": "检查器",
        "tab_options": "选项",
        "opt_format": "数值格式",
        "opt_fmt_si": "工程(SI)",
        "opt_fmt_sci": "科学计数法",
        "opt_sig": "有效数字",
        "opt_max_abs": "极大阈值(>标注)",
        "opt_min_abs": "极小阈值(~0标注)",
        "opt_show_shortcuts": "显示快捷卡片",
        "opt_show_labels": "在画布显示数值标签",
        "opt_defaults": "默认参数",
        "opt_def_source_v": "电源电压 V",
        "opt_def_source_iwarn": "电源过流阈值 A",
        "opt_def_res_r": "电阻 R",
        "opt_def_rheo_r": "滑变 R",
        "opt_def_rheo_min": "滑变 Rmin",
        "opt_def_rheo_max": "滑变 Rmax",
        "opt_def_amm_burden": "电流表 burden_V",
        "opt_def_volt_sens": "电压表 ohm_per_V",
        "opt_def_gal_r": "检流计 Rcoil",
        "opt_def_gal_ifs": "检流计 Ifs",
        "apply": "应用",
        "options": "⚙ 选项",
        "locked": "已锁定",
    },
}

class CircuitGUI:
    def __init__(self, root):
        self.root = root
        self.lang = "zh"
        self.root.title("Circuit Simulator - GUI")
        self.root.geometry("1400x800")
        
        self.cir = Circuit()
        self.result = SolveResult(ok=True)
        self.history = CircuitHistory()
        self.mode = "navigate"
        self.place_type = "wire"
        self.wire_start: Optional[Point] = None
        self.selected_comp: Optional[Component] = None
        self.hover_comp: Optional[Component] = None
        self._last_motion_grid: Optional[Point] = None
        self._hover_after_id: Optional[str] = None
        self._pending_motion_grid: Optional[Point] = None
        self._slider_after_id: Optional[str] = None
        self._inspector_comp_id: Optional[str] = None
        self._wire_preview_end: Optional[Point] = None

        self._drag_active: bool = False
        self._drag_comp: Optional[Component] = None
        self._drag_kind: str = ""
        self._drag_start_grid: Optional[Point] = None
        self._drag_start_a: Optional[Point] = None
        self._drag_start_b: Optional[Point] = None
        self._drag_moved: bool = False

        self._rslider_after_id: Optional[str] = None
        self._wheel_after_id: Optional[str] = None

        self._slider_after_id: Optional[str] = None

        self._fmt_style: str = "si"
        self._fmt_sig: int = 3
        self._fmt_max_abs: float = 1e12
        self._fmt_min_abs: float = 1e-15

        self._opt_show_shortcuts: bool = True
        self._opt_show_labels: bool = True

        self._options_win: Optional[tk.Toplevel] = None

        self.defaults: Dict[str, float] = {
            "socket_V": 5.0,
            "socket_Iwarn": 5.0,
            "socket_Vmin": 0.0,
            "socket_Vmax": 12.0,
            "resistor_R": 100.0,
            "resistor_Rmin": 1.0,
            "resistor_Rmax": 1e6,
            "rheostat_R": 200.0,
            "rheostat_Rmin": 0.0,
            "rheostat_Rmax": 500.0,
            "ammeter_burden_V": 0.05,
            "voltmeter_ohm_per_V": 20000.0,
            "galv_Rcoil": 50.0,
            "galv_Ifs": 50e-6,
        }

        self._i18n_widgets: Dict[str, Any] = {}
        
        self.setup_ui()
        self.root.title(self.tr("app_title"))
        self._apply_i18n()
        self.load_example_circuit()
        self.history.record(self.cir)
        self.solve()
        self.redraw()

    def open_options(self):
        if self._options_win is not None:
            try:
                self._options_win.deiconify()
                self._options_win.lift()
                return
            except Exception:
                self._options_win = None

        win = tk.Toplevel(self.root)
        self._options_win = win
        win.title(self.tr("tab_options"))
        win.geometry("360x620")
        win.transient(self.root)

        def on_close():
            try:
                win.destroy()
            finally:
                self._options_win = None

        win.protocol("WM_DELETE_WINDOW", on_close)
        self._build_options(win)

    def fmt(self, x: float, unit: str) -> str:
        return format_value(
            x,
            unit,
            style=str(self._fmt_style),
            max_abs=float(self._fmt_max_abs),
            min_abs=float(self._fmt_min_abs),
            sig=int(self._fmt_sig),
        )

    def _mid_canvas(self, comp: Component) -> Tuple[int, int]:
        x1, y1 = self.grid_to_canvas(comp.a)
        x2, y2 = self.grid_to_canvas(comp.b)
        return (x1 + x2) // 2, (y1 + y2) // 2

    def _is_locked(self, comp: Component) -> bool:
        try:
            return str(comp.meta.get("locked", "0")) == "1"
        except Exception:
            return False

    def _tr_comp(self, ctype: str) -> str:
        k = f"comp_{ctype}"
        s = self.tr(k)
        return ctype if s == k else s

    def _flag_text(self, flag: Optional[str]) -> Optional[str]:
        if not flag:
            return None
        k = f"flag_{flag}"
        s = self.tr(k)
        return flag if s == k else s

    def tr(self, key: str, **kwargs) -> str:
        table = I18N.get(self.lang, I18N.get("en", {}))
        s = table.get(key)
        if s is None:
            s = I18N.get("en", {}).get(key, key)
        try:
            return s.format(**kwargs)
        except Exception:
            return s

    def set_language(self, lang: str):
        if lang not in I18N:
            return
        self.lang = lang
        self.root.title(self.tr("app_title"))
        self._apply_i18n()
        self.refresh_inspector()
        self.update_info_panel()

    def _apply_i18n(self):
        w = self._i18n_widgets
        if w.get("lbl_palette"):
            w["lbl_palette"].config(text=self.tr("component_palette"))
        if w.get("lbl_actions"):
            w["lbl_actions"].config(text=self.tr("actions"))
        if w.get("inspector"):
            w["inspector"].config(text=self.tr("inspector"))
        if w.get("btn_solve"):
            w["btn_solve"].config(text=self.tr("solve"))
        if w.get("btn_goal_seek"):
            w["btn_goal_seek"].config(text=self.tr("goal_seek"))
        if w.get("btn_wire"):
            w["btn_wire"].config(text=self.tr("wire_tool"))
        if w.get("btn_nav"):
            w["btn_nav"].config(text=self.tr("navigate"))
        if w.get("btn_save"):
            w["btn_save"].config(text=self.tr("save"))
        if w.get("btn_load"):
            w["btn_load"].config(text=self.tr("load"))
        if w.get("btn_clear"):
            w["btn_clear"].config(text=self.tr("clear_all"))
        if w.get("btn_options"):
            w["btn_options"].config(text=self.tr("options"))
        if w.get("lbl_lang"):
            w["lbl_lang"].config(text=self.tr("language") + ":")
        if w.get("lang_cb"):
            try:
                w["lang_cb"].config(values=[self.tr("lang_zh"), self.tr("lang_en")])
                w["lang_cb"].current(0 if self.lang == "zh" else 1)
            except Exception:
                pass
        if w.get("mode_label"):
            if self.mode == "navigate":
                w["mode_label"].config(text=self.tr("mode_navigate"))
            elif self.mode == "wire":
                w["mode_label"].config(text=self.tr("mode_wire"))
            elif self.mode == "place":
                w["mode_label"].config(text=self.tr("mode_place", ctype=self._tr_comp(self.place_type)))

        cards = getattr(self, "_status_cards", {})
        for c in cards.values():
            try:
                c["title"].config(text=self.tr(c.get("title_key", "")))
            except Exception:
                pass

        if self._options_win is not None:
            try:
                self._options_win.title(self.tr("tab_options"))
            except Exception:
                pass
        for k in (
            "lbl_opt_format",
            "lbl_opt_sig",
            "lbl_opt_max",
            "lbl_opt_min",
            "chk_show_shortcuts",
            "lbl_opt_defaults",
            "btn_opt_apply",
            "lbl_def_source_v",
            "lbl_def_source_iwarn",
            "lbl_def_res_r",
            "lbl_def_rheo_r",
            "lbl_def_rheo_min",
            "lbl_def_rheo_max",
            "lbl_def_amm_burden",
            "lbl_def_volt_sens",
            "lbl_def_gal_r",
            "lbl_def_gal_ifs",
        ):
            if w.get(k):
                try:
                    w[k].config(text=self.tr(w[k].i18n_key) if hasattr(w[k], "i18n_key") else w[k].cget("text"))
                except Exception:
                    pass
        if w.get("cb_opt_format"):
            try:
                w["cb_opt_format"].config(values=[self.tr("opt_fmt_si"), self.tr("opt_fmt_sci")])
            except Exception:
                pass

    def _record_history(self):
        self.history.record(self.cir)

    def _undo(self):
        if self.history.undo(self.cir):
            self.selected_comp = None
            self.hover_comp = None
            self.wire_start = None
            self._wire_preview_end = None
            self.solve_and_redraw()
            self.status_label.config(text=self.tr("undo"))
        else:
            self.status_label.config(text=self.tr("nothing_to_undo"))

    def _redo(self):
        if self.history.redo(self.cir):
            self.selected_comp = None
            self.hover_comp = None
            self.wire_start = None
            self._wire_preview_end = None
            self.solve_and_redraw()
            self.status_label.config(text=self.tr("redo"))
        else:
            self.status_label.config(text=self.tr("nothing_to_redo"))

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_panel = ttk.Frame(main_frame, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        lbl_palette = ttk.Label(left_panel, text=self.tr("component_palette"), font=("Arial", 12, "bold"))
        lbl_palette.pack(pady=5)
        self._i18n_widgets["lbl_palette"] = lbl_palette
        
        components = [
            ("socket", "⎍"),
            ("wire", "·"),
            ("resistor", "Ω"),
            ("bulb", "💡"),
            ("rheostat", "≋"),
            ("switch_spst", "⏻"),
            ("switch_spdt", "⇄"),
            ("switch_sp3t", "⤨"),
            ("switch_dpst", "⏻"),
            ("switch_dpdt", "⏻"),
            ("button_momentary", "⏺"),
            ("ammeter", "A"),
            ("voltmeter", "V"),
            ("galvanometer", "G"),
        ]
        
        for ctype, symbol in components:
            btn = ttk.Button(
                left_panel, 
                text=f"{symbol} {self._tr_comp(ctype)}",
                command=lambda t=ctype: self.select_component(t)
            )
            btn.pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        lbl_actions = ttk.Label(left_panel, text=self.tr("actions"), font=("Arial", 12, "bold"))
        lbl_actions.pack(pady=5)
        self._i18n_widgets["lbl_actions"] = lbl_actions
        
        btn_solve = ttk.Button(left_panel, text=self.tr("solve"), command=self.solve_and_redraw)
        btn_goal_seek = ttk.Button(left_panel, text=self.tr("goal_seek"), command=self.open_goal_seek)
        btn_wire = ttk.Button(left_panel, text=self.tr("wire_tool"), command=self.set_mode_wire)
        btn_nav = ttk.Button(left_panel, text=self.tr("navigate"), command=self.set_mode_navigate)
        btn_save = ttk.Button(left_panel, text=self.tr("save"), command=self.save)
        btn_load = ttk.Button(left_panel, text=self.tr("load"), command=self.load)
        btn_clear = ttk.Button(left_panel, text=self.tr("clear_all"), command=self.clear_all)
        btn_options = ttk.Button(left_panel, text=self.tr("options"), command=self.open_options)

        btn_solve.pack(fill=tk.X, pady=2, padx=5)
        btn_goal_seek.pack(fill=tk.X, pady=2, padx=5)
        btn_wire.pack(fill=tk.X, pady=2, padx=5)
        btn_nav.pack(fill=tk.X, pady=2, padx=5)
        btn_save.pack(fill=tk.X, pady=2, padx=5)
        btn_load.pack(fill=tk.X, pady=2, padx=5)
        btn_clear.pack(fill=tk.X, pady=2, padx=5)
        btn_options.pack(fill=tk.X, pady=(8, 2), padx=5)

        self._i18n_widgets["btn_solve"] = btn_solve
        self._i18n_widgets["btn_goal_seek"] = btn_goal_seek
        self._i18n_widgets["btn_wire"] = btn_wire
        self._i18n_widgets["btn_nav"] = btn_nav
        self._i18n_widgets["btn_save"] = btn_save
        self._i18n_widgets["btn_load"] = btn_load
        self._i18n_widgets["btn_clear"] = btn_clear
        self._i18n_widgets["btn_options"] = btn_options

        self.inspector = ttk.Labelframe(left_panel, text=self.tr("inspector"))
        self.inspector.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        self.inspector_body = ttk.Frame(self.inspector)
        self.inspector_body.pack(fill=tk.BOTH, expand=True)
        self._i18n_widgets["inspector"] = self.inspector
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        self.mode_label = ttk.Label(toolbar, text=self.tr("mode_navigate"), font=("Arial", 10))
        self.mode_label.pack(side=tk.LEFT, padx=5)
        self._i18n_widgets["mode_label"] = self.mode_label
        
        self.status_label = ttk.Label(toolbar, text=self.tr("status_ready"), font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=20)

        self._lang_codes = ["zh", "en"]
        lbl_lang = ttk.Label(toolbar, text=self.tr("language") + ":")
        lbl_lang.pack(side=tk.RIGHT, padx=(6, 2))
        self._i18n_widgets["lbl_lang"] = lbl_lang

        lang_cb = ttk.Combobox(toolbar, state="readonly", width=10)
        lang_cb.pack(side=tk.RIGHT, padx=(2, 10))
        self._i18n_widgets["lang_cb"] = lang_cb
        lang_cb.config(values=[self.tr("lang_zh"), self.tr("lang_en")])
        lang_cb.current(0 if self.lang == "zh" else 1)

        def on_lang(_e):
            idx = int(lang_cb.current())
            if 0 <= idx < len(self._lang_codes):
                self.set_language(self._lang_codes[idx])

        lang_cb.bind("<<ComboboxSelected>>", on_lang)
        
        canvas_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=CANVAS_W, height=CANVAS_H)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<MouseWheel>", self.on_canvas_mousewheel)

        self.root.bind_all("<Key>", self.on_key)
        
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, pady=(5, 0))

        self._status_cards: Dict[str, Any] = {}
        self._card_fonts = {
            "title": tkfont.Font(family="Arial", size=10, weight="bold"),
            "body": tkfont.Font(family="Arial", size=10),
            "mono": tkfont.Font(family="Courier", size=10),
        }

        grid = tk.Frame(info_frame, bg="#f7f7fb")
        grid.pack(fill=tk.BOTH, expand=True)
        for r in range(2):
            grid.rowconfigure(r, weight=1)
        for c in range(2):
            grid.columnconfigure(c, weight=1)

        def make_card(key: str, title_key: str, r: int, c: int):
            frame = tk.Frame(grid, bg="#ffffff", highlightbackground="#d0d0d0", highlightthickness=1)
            frame.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
            ttl = tk.Label(frame, text=self.tr(title_key), bg="#ffffff", fg="#222222", font=self._card_fonts["title"], anchor="w")
            ttl.pack(fill=tk.X, padx=8, pady=(6, 2))
            val = tk.Label(frame, text="", bg="#ffffff", fg="#222222", font=self._card_fonts["body"], justify=tk.LEFT, anchor="nw")
            val.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
            self._status_cards[key] = {"frame": frame, "title": ttl, "value": val, "title_key": title_key}

        make_card("sel", "panel_selection", 0, 0)
        make_card("meas", "panel_measurements", 0, 1)
        make_card("stat", "panel_status", 1, 0)
        make_card("keys", "panel_shortcuts", 1, 1)

    def refresh_inspector(self):
        comp = self.selected_comp
        cid = comp.cid if comp else None
        if cid == self._inspector_comp_id:
            return
        self._inspector_comp_id = cid
        for w in self.inspector_body.winfo_children():
            w.destroy()

        if not comp:
            ttk.Label(self.inspector_body, text=self.tr("no_selection")).pack(anchor=tk.W, padx=5, pady=5)
            return

        ttk.Label(self.inspector_body, text=f"{comp.display_name()}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.inspector_body, text=f"{self.tr('info_type')}: {self._tr_comp(comp.ctype)}").pack(anchor=tk.W, padx=5, pady=2)

        if comp.ctype == "rheostat":
            Rmin = float(comp.props.get("Rmin", 0.0))
            Rmax = float(comp.props.get("Rmax", max(float(comp.props.get("R", 100.0)), 100.0)))
            if Rmax < Rmin:
                Rmin, Rmax = Rmax, Rmin
            ttk.Label(self.inspector_body, text=f"R = {comp.props.get('R', 0.0)}Ω").pack(anchor=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=float(comp.props.get("R", Rmin)))

            def on_slide(_v):
                comp.props["Rmin"] = Rmin
                comp.props["Rmax"] = Rmax
                comp.props["R"] = float(var.get())
                if self._slider_after_id is not None:
                    try:
                        self.root.after_cancel(self._slider_after_id)
                    except Exception:
                        pass
                self._slider_after_id = self.root.after(60, self.solve_and_redraw)

            scale = ttk.Scale(self.inspector_body, from_=Rmin, to=Rmax, orient=tk.HORIZONTAL, variable=var, command=on_slide)
            scale.pack(fill=tk.X, padx=5, pady=5)

        if comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
            ranges = meter_ranges(comp)
            if ranges:
                unit = "V" if comp.ctype == "voltmeter" else "A"
                items = [f"{i}: {format_si_safe(r, unit)}" for i, r in enumerate(ranges)]
                cur = int(comp.props.get("range", 0))
                if cur < 0:
                    cur = 0
                if cur >= len(items):
                    cur = len(items) - 1
                ttk.Label(self.inspector_body, text=self.tr("range")).pack(anchor=tk.W, padx=5, pady=(8, 2))
                cb = ttk.Combobox(self.inspector_body, values=items, state="readonly")
                cb.current(cur)

                def on_pick(_e):
                    comp.props["range"] = int(cb.current())
                    self.solve_and_redraw()

                cb.bind("<<ComboboxSelected>>", on_pick)
                cb.pack(fill=tk.X, padx=5, pady=2)
            else:
                ttk.Label(self.inspector_body, text=self.tr("no_ranges")).pack(anchor=tk.W, padx=5, pady=2)

        if comp.ctype == "switch_spst":
            v = tk.IntVar(value=int(comp.props.get("state", 1)))

            def on_toggle():
                comp.props["state"] = int(v.get())
                self.solve_and_redraw()

            ttk.Checkbutton(self.inspector_body, text=self.tr("closed"), variable=v, command=on_toggle).pack(anchor=tk.W, padx=5, pady=6)

        if comp.ctype in ("switch_spdt", "switch_dpdt"):
            cur = int(comp.props.get("throw", 0))
            cb = ttk.Combobox(self.inspector_body, values=["0", "1"], state="readonly")
            cb.current(0 if cur == 0 else 1)

            def on_pick(_e):
                comp.props["throw"] = int(cb.get())
                self.solve_and_redraw()

            ttk.Label(self.inspector_body, text=self.tr("throw")).pack(anchor=tk.W, padx=5, pady=(8, 2))
            cb.bind("<<ComboboxSelected>>", on_pick)
            cb.pack(fill=tk.X, padx=5, pady=2)

        if comp.ctype == "switch_sp3t":
            cur = int(comp.props.get("throw", 0))
            if cur < 0:
                cur = 0
            if cur > 2:
                cur = 2
            cb = ttk.Combobox(self.inspector_body, values=["0", "1", "2"], state="readonly")
            cb.current(cur)

            def on_pick(_e):
                comp.props["throw"] = int(cb.get())
                self.solve_and_redraw()

            ttk.Label(self.inspector_body, text=self.tr("throw")).pack(anchor=tk.W, padx=5, pady=(8, 2))
            cb.bind("<<ComboboxSelected>>", on_pick)
            cb.pack(fill=tk.X, padx=5, pady=2)

        if comp.ctype == "switch_dpst":
            v = tk.IntVar(value=int(comp.props.get("state", 1)))

            def on_toggle():
                comp.props["state"] = int(v.get())
                self.solve_and_redraw()

            ttk.Checkbutton(self.inspector_body, text=self.tr("closed"), variable=v, command=on_toggle).pack(anchor=tk.W, padx=5, pady=6)

        if comp.ctype == "button_momentary":
            ttk.Label(self.inspector_body, text=self.tr("momentary_button")).pack(anchor=tk.W, padx=5, pady=(8, 2))
            bf = ttk.Frame(self.inspector_body)
            bf.pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(bf, text=self.tr("press"), command=lambda: self.set_momentary(comp, 1)).pack(side=tk.LEFT, padx=2)
            ttk.Button(bf, text=self.tr("release"), command=lambda: self.set_momentary(comp, 0)).pack(side=tk.LEFT, padx=2)

    def load_example_circuit(self):
        self.cir.add("socket", (6, 6), (6, 18), V=6.0, Iwarn=5.0)
        self.cir.add("resistor", (6, 6), (30, 6), R=20.0)
        self.cir.add("wire", (30, 6), (30, 18))
        self.cir.add("wire", (30, 18), (6, 18))

    def select_component(self, ctype: str):
        self.place_type = ctype
        self.mode = "place"
        self.mode_label.config(text=self.tr("mode_place", ctype=self._tr_comp(ctype)))
        self.status_label.config(text=self.tr("status_place", ctype=self._tr_comp(ctype)))

    def set_mode_navigate(self):
        self.mode = "navigate"
        self.wire_start = None
        self._wire_preview_end = None
        self.mode_label.config(text=self.tr("mode_navigate"))
        self.status_label.config(text=self.tr("status_navigate"))
        self.redraw()

    def set_mode_wire(self):
        self.mode = "wire"
        self.wire_start = None
        self._wire_preview_end = None
        self.mode_label.config(text=self.tr("mode_wire"))
        self.status_label.config(text=self.tr("status_wire"))
        self.redraw()

    def on_key(self, event):
        ks = event.keysym
        # Undo/redo: support both Ctrl and Command (Mac)
        if (event.state & 0x4) and ks.lower() == "z":
            if event.state & 0x1:
                self._redo()
            else:
                self._undo()
            return
        if (event.state & 0x4) and ks.lower() == "y":
            self._redo()
            return
        if ks in ("Escape",):
            if self._drag_active:
                self._cancel_drag()
                return
            if self.wire_start is not None or self.mode == "wire":
                self.wire_start = None
                self._wire_preview_end = None
                self.set_mode_navigate()
            return

        if ks == "space":
            if self.mode == "wire":
                self.set_mode_navigate()
            else:
                self.set_mode_wire()
            return

        if ks.lower() == "e":
            if self.selected_comp:
                self.edit_component(self.selected_comp)
            return

        if ks in ("Left", "Right", "Up", "Down") and self.selected_comp and self.mode == "navigate":
            step = 5 if (event.state & 0x1) else 1
            dx, dy = 0, 0
            if ks == "Left":
                dx = -step
            elif ks == "Right":
                dx = step
            elif ks == "Up":
                dy = -step
            elif ks == "Down":
                dy = step
            self._nudge_selected(dx, dy)
            return

        ch = getattr(event, "char", "") or ""
        if (len(ch) == 1) and ch.isdigit() and (ch != "0") and not (event.state & 0x4):
            mapping = [
                "wire",
                "resistor",
                "bulb",
                "rheostat",
                "socket",
                "ammeter",
                "voltmeter",
                "galvanometer",
                "switch_spst",
            ]
            idx = int(ch) - 1
            if 0 <= idx < len(mapping):
                self.select_component(mapping[idx])
            return

        if ks in ("Delete", "BackSpace"):
            if self.selected_comp:
                self.delete_component(self.selected_comp)
            return

        if (event.state & 0x4) and ks.lower() == "s":
            self.save()
            return
        if (event.state & 0x4) and ks.lower() == "o":
            self.load()
            return
        if (event.state & 0x4) and ks.lower() == "r":
            self.solve_and_redraw()
            return
        if (event.state & 0x4) and ks.lower() == "n":
            self.clear_all()
            return

        if (event.state & 0x4) and ks.lower() == "g":
            self.open_goal_seek()
            return

        if ks.lower() == "w":
            self.set_mode_wire()
            return
        if ks.lower() == "n":
            self.set_mode_navigate()
            return

    def open_goal_seek(self):
        dlg = GoalSeekDialog(self.root, self.cir, self.selected_comp, tr=self.tr, tr_comp=self._tr_comp)
        if not dlg.result:
            return
        if dlg.result.get("auto_range"):
            ms = dlg.result.get("measure", {})
            if ms.get("kind") == "comp":
                mcid = ms.get("cid")
                field = ms.get("field")
                ab = bool(ms.get("abs"))
                mcomp = self.cir.components.get(mcid) if mcid else None
                if mcomp and ab:
                    rngs = meter_ranges(mcomp)
                    if rngs and field in ("Iab", "Vab"):
                        tgt = abs(float(dlg.result.get("target", 0.0)))
                        idx = 0
                        while idx < len(rngs) and abs(float(rngs[idx])) < tgt:
                            idx += 1
                        if idx >= len(rngs):
                            idx = len(rngs) - 1
                        try:
                            mcomp.props["range"] = int(idx)
                        except Exception:
                            pass
        try:
            gs = goal_seek_parameter(
                self.cir,
                var_cid=dlg.result["var_cid"],
                var_prop=dlg.result["var_prop"],
                target=float(dlg.result["target"]),
                measure=dlg.result["measure"],
                lo=float(dlg.result["lo"]),
                hi=float(dlg.result["hi"]),
                reject_if_overcurrent=bool(dlg.result.get("reject_overcurrent", False)),
            )
        except Exception as e:
            messagebox.showerror(self.tr("gs_dialog_title"), str(e))
            return

        if gs.ok:
            self.solve()
            self._record_history()
            self.redraw()
            self.status_label.config(text=f"Goal seek ok: {dlg.result['var_prop']}={gs.value:.6g} (achieved={gs.achieved:.6g})")
        else:
            messagebox.showerror(self.tr("gs_dialog_title"), f"Failed: {gs.message}\nBest={gs.value:.6g} achieved={gs.achieved:.6g}")

    def grid_snap(self, x: int, y: int) -> Point:
        gx = round(x / GRID_SIZE)
        gy = round(y / GRID_SIZE)
        return (gx, gy)

    def grid_to_canvas(self, p: Point) -> Tuple[int, int]:
        return (p[0] * GRID_SIZE, p[1] * GRID_SIZE)

    def on_canvas_click(self, event):
        grid_pos = self.grid_snap(event.x, event.y)
        
        if self.mode == "place":
            self.place_component(grid_pos)
        elif self.mode == "wire":
            self.toggle_wire(grid_pos)
        else:
            comp = self.cir.find_near(grid_pos)
            self.selected_comp = comp
            self.redraw()

    def on_canvas_press(self, event):
        grid_pos = self.grid_snap(event.x, event.y)

        if self.mode == "place":
            self.place_component(grid_pos)
            return
        if self.mode == "wire":
            self.toggle_wire(grid_pos)
            return

        comp = self.cir.find_near(grid_pos)
        self.selected_comp = comp
        if comp and comp.ctype != "button_momentary":
            self._begin_drag_candidate(comp, grid_pos, canvas_xy=(event.x, event.y))
        if comp and comp.ctype == "button_momentary":
            comp.props["pressed"] = 1
            self.solve()
            self._record_history()
        self._inspector_comp_id = None
        self.redraw()

    def on_canvas_release(self, _event):
        if self._drag_active:
            comp = self._drag_comp
            kind = self._drag_kind
            moved = self._end_drag()
            if (not moved) and comp is not None and kind not in ("rslider", "vslider", "reslider"):
                self._click_component(comp)
            return
        comp = self.selected_comp
        if comp and comp.ctype == "button_momentary":
            if int(comp.props.get("pressed", 0)) == 1:
                comp.props["pressed"] = 0
                self.solve()
                self._record_history()
                self.redraw()

    def _click_component(self, comp: Component) -> None:
        if self._is_locked(comp):
            return
        changed = False
        if comp.ctype in ("switch_spst", "switch_dpst"):
            st = int(comp.props.get("state", 1))
            comp.props["state"] = 0 if st == 1 else 1
            changed = True
        elif comp.ctype in ("switch_spdt", "switch_dpdt"):
            th = int(comp.props.get("throw", 0))
            comp.props["throw"] = 0 if th == 1 else 1
            changed = True
        elif comp.ctype == "switch_sp3t":
            th = int(comp.props.get("throw", 0))
            comp.props["throw"] = int((th + 1) % 3)
            changed = True
        if changed:
            self._inspector_comp_id = None
            self.solve()
            self._record_history()
            self.redraw()

    def on_canvas_mousewheel(self, event):
        comp = self.hover_comp or self.selected_comp
        if not comp:
            return
        if self._is_locked(comp):
            return
        try:
            delta = int(getattr(event, "delta", 0))
        except Exception:
            delta = 0
        if delta == 0:
            return

        shift = (getattr(event, "state", 0) & 0x1) != 0

        changed = False
        if comp.ctype == "rheostat":
            step = 1.0 if delta > 0 else -1.0
            if shift:
                step *= 10.0
            R = float(comp.props.get("R", self.defaults.get("rheostat_R", 200.0)))
            Rmin = float(comp.props.get("Rmin", self.defaults.get("rheostat_Rmin", 0.0)))
            Rmax = float(comp.props.get("Rmax", self.defaults.get("rheostat_Rmax", max(R, 100.0))))
            if Rmax < Rmin:
                Rmin, Rmax = Rmax, Rmin
            R2 = R + step
            if R2 < Rmin:
                R2 = Rmin
            if R2 > Rmax:
                R2 = Rmax
            comp.props["R"] = float(R2)
            changed = True
        elif comp.ctype == "socket":
            step = 0.1 if delta > 0 else -0.1
            if shift:
                step *= 10.0
            V = float(comp.props.get("V", self.defaults.get("socket_V", 5.0)))
            comp.props["V"] = float(V + step)
            changed = True
        elif comp.ctype == "resistor":
            step = 1.0 if delta > 0 else -1.0
            if shift:
                step *= 10.0
            R = float(comp.props.get("R", self.defaults.get("resistor_R", 100.0)))
            R2 = R + step
            if R2 < 0.01:
                R2 = 0.01
            comp.props["R"] = float(R2)
            changed = True
        elif comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
            rngs = meter_ranges(comp)
            if rngs:
                cur = int(comp.props.get("range", 0))
                cur = max(0, min(cur, len(rngs) - 1))
                nxt = cur + (1 if delta > 0 else -1)
                nxt = max(0, min(nxt, len(rngs) - 1))
                if nxt != cur:
                    comp.props["range"] = int(nxt)
                    changed = True

        if not changed:
            return
        if self._wheel_after_id is not None:
            try:
                self.root.after_cancel(self._wheel_after_id)
            except Exception:
                pass
        self._wheel_after_id = self.root.after(60, self._apply_wheel_change)

    def _apply_wheel_change(self):
        self._wheel_after_id = None
        self.solve()
        self._record_history()
        self.redraw()

    def on_canvas_drag(self, event):
        if self.mode != "navigate":
            return
        if not self._drag_active:
            return
        if self._drag_comp is None or self._drag_start_grid is None:
            return
        grid_pos = self.grid_snap(event.x, event.y)
        if grid_pos == self._drag_start_grid and not self._drag_moved:
            return

        comp = self._drag_comp
        if self._drag_kind == "rslider":
            self._update_rheostat_slider(comp, event.x, event.y)
        elif self._drag_kind == "vslider":
            self._update_socket_slider(comp, event.x, event.y)
        elif self._drag_kind == "reslider":
            self._update_resistor_slider(comp, event.x, event.y)
        elif self._drag_kind == "whole":
            if self._drag_start_a is None or self._drag_start_b is None:
                return
            dx = grid_pos[0] - self._drag_start_grid[0]
            dy = grid_pos[1] - self._drag_start_grid[1]
            self._translate_component(comp, dx, dy, base_a=self._drag_start_a, base_b=self._drag_start_b)
        elif self._drag_kind == "a":
            comp.a = grid_pos
        elif self._drag_kind == "b":
            comp.b = grid_pos

        self._drag_moved = True
        self.hover_comp = None
        self._pending_motion_grid = None
        self.redraw()

    def _begin_drag_candidate(self, comp: Component, grid_pos: Point, *, canvas_xy: Optional[Tuple[int, int]] = None):
        if self._is_locked(comp):
            return

        if canvas_xy is not None:
            cx, cy = canvas_xy
            c_mx, c_my = self._mid_canvas(comp)

            if comp.ctype == "rheostat":
                if abs(cy - (c_my + 14)) <= 8 and abs(cx - c_mx) <= 22:
                    self._start_slider_drag(comp, grid_pos, "rslider")
                    return

            if comp.ctype == "socket":
                if abs(cy - (c_my + 22)) <= 10 and abs(cx - c_mx) <= 26:
                    self._start_slider_drag(comp, grid_pos, "vslider")
                    return

            if comp.ctype == "resistor":
                if abs(cy - (c_my + 18)) <= 10 and abs(cx - c_mx) <= 30:
                    self._start_slider_drag(comp, grid_pos, "reslider")
                    return

        da = abs(comp.a[0] - grid_pos[0]) + abs(comp.a[1] - grid_pos[1])
        db = abs(comp.b[0] - grid_pos[0]) + abs(comp.b[1] - grid_pos[1])
        if da <= 1 and da <= db:
            kind = "a"
        elif db <= 1 and db < da:
            kind = "b"
        else:
            kind = "whole"

        self._drag_active = True
        self._drag_comp = comp
        self._drag_kind = kind
        self._drag_start_grid = grid_pos
        self._drag_start_a = comp.a
        self._drag_start_b = comp.b
        self._drag_moved = False
        try:
            self.canvas.config(cursor="fleur" if kind == "whole" else "crosshair")
        except Exception:
            pass

    def _start_slider_drag(self, comp: Component, grid_pos: Point, kind: str):
        self._drag_active = True
        self._drag_comp = comp
        self._drag_kind = kind
        self._drag_start_grid = grid_pos
        self._drag_start_a = comp.a
        self._drag_start_b = comp.b
        self._drag_moved = False
        try:
            self.canvas.config(cursor="sb_h_double_arrow")
        except Exception:
            pass

    def _cancel_drag(self):
        if not self._drag_active or self._drag_comp is None:
            self._drag_active = False
            self._drag_comp = None
            return
        if self._drag_start_a is not None:
            self._drag_comp.a = self._drag_start_a
        if self._drag_start_b is not None:
            self._drag_comp.b = self._drag_start_b
        self._drag_active = False
        self._drag_comp = None
        self._drag_kind = ""
        self._drag_start_grid = None
        self._drag_start_a = None
        self._drag_start_b = None
        self._drag_moved = False
        try:
            self.canvas.config(cursor="")
        except Exception:
            pass
        self.redraw()

    def _end_drag(self) -> bool:
        moved = self._drag_moved
        self._drag_active = False
        self._drag_comp = None
        self._drag_kind = ""
        self._drag_start_grid = None
        self._drag_start_a = None
        self._drag_start_b = None
        self._drag_moved = False
        if moved and self._slider_after_id is not None:
            try:
                self.root.after_cancel(self._slider_after_id)
            except Exception:
                pass
            self._slider_after_id = None
        if moved:
            self.solve()
            self._record_history()
            self.redraw()
        try:
            self.canvas.config(cursor="")
        except Exception:
            pass
        return moved

    def _schedule_slider_solve(self):
        if self._slider_after_id is not None:
            try:
                self.root.after_cancel(self._slider_after_id)
            except Exception:
                pass
        self._slider_after_id = self.root.after(60, self.solve_and_redraw)


    def _update_rheostat_slider(self, comp: Component, cx: int, cy: int):
        Rmin = float(comp.props.get("Rmin", self.defaults.get("rheostat_Rmin", 0.0)))
        Rmax = float(comp.props.get("Rmax", self.defaults.get("rheostat_Rmax", 500.0)))
        if Rmax < Rmin:
            Rmin, Rmax = Rmax, Rmin
        if abs(Rmax - Rmin) < 1e-12:
            return
        mx, my = self._mid_canvas(comp)
        horizontal = abs(comp.b[0] - comp.a[0]) >= abs(comp.b[1] - comp.a[1])
        if horizontal:
            t = (cx - (mx - 12)) / float((mx + 12) - (mx - 12))
        else:
            t = (cy - (my - 12)) / float((my + 12) - (my - 12))
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        comp.props["R"] = float(Rmin + t * (Rmax - Rmin))
        self._drag_moved = True
        self._schedule_slider_solve()

    def _update_socket_slider(self, comp: Component, cx: int, _cy: int):
        Vmin = float(self.defaults.get("socket_Vmin", 0.0))
        Vmax = float(self.defaults.get("socket_Vmax", 12.0))
        if Vmax < Vmin:
            Vmin, Vmax = Vmax, Vmin
        if abs(Vmax - Vmin) < 1e-12:
            return
        mx, my = self._mid_canvas(comp)
        t = (cx - (mx - 18)) / float((mx + 18) - (mx - 18))
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        comp.props["V"] = float(Vmin + t * (Vmax - Vmin))
        self._drag_moved = True
        self._schedule_slider_solve()

    def _update_resistor_slider(self, comp: Component, cx: int, _cy: int):
        Rmin = float(self.defaults.get("resistor_Rmin", 1.0))
        Rmax = float(self.defaults.get("resistor_Rmax", 1e6))
        if Rmax < Rmin:
            Rmin, Rmax = Rmax, Rmin
        if Rmin <= 0.0:
            Rmin = 1e-6
        if abs(math.log10(Rmax) - math.log10(Rmin)) < 1e-12:
            return
        mx, my = self._mid_canvas(comp)
        t = (cx - (mx - 22)) / float((mx + 22) - (mx - 22))
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        logr = math.log10(Rmin) + t * (math.log10(Rmax) - math.log10(Rmin))
        comp.props["R"] = float(10 ** logr)
        self._drag_moved = True
        self._schedule_slider_solve()

    def _translate_component(self, comp: Component, dx: int, dy: int, *, base_a: Point, base_b: Point):
        comp.a = (base_a[0] + dx, base_a[1] + dy)
        comp.b = (base_b[0] + dx, base_b[1] + dy)
        for k in list(comp.props.keys()):
            if k.endswith("_x"):
                try:
                    comp.props[k] = float(comp.props[k]) + dx
                except Exception:
                    pass
            if k.endswith("_y"):
                try:
                    comp.props[k] = float(comp.props[k]) + dy
                except Exception:
                    pass

    def _nudge_selected(self, dx: int, dy: int):
        comp = self.selected_comp
        if not comp:
            return
        if self._is_locked(comp):
            return
        self._translate_component(comp, dx, dy, base_a=comp.a, base_b=comp.b)
        self.solve()
        self._record_history()
        self.redraw()

    def on_canvas_right_click(self, event):
        grid_pos = self.grid_snap(event.x, event.y)
        comp = self.cir.find_near(grid_pos)
        
        if comp:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=self.tr("menu_edit"), command=lambda: self.edit_component(comp))
            menu.add_command(label=self.tr("menu_delete"), command=lambda: self.delete_component(comp))
            menu.add_command(label=self.tr("menu_duplicate"), command=lambda: self._duplicate_component(comp))
            if self._is_locked(comp):
                menu.add_command(label=self.tr("menu_unlock"), command=lambda: self._toggle_lock(comp, False))
            else:
                menu.add_command(label=self.tr("menu_lock"), command=lambda: self._toggle_lock(comp, True))
            if comp.ctype in ("switch_spst", "switch_dpst"):
                menu.add_separator()
                menu.add_command(label=self.tr("menu_toggle"), command=lambda: self._click_component(comp))
            if comp.ctype in ("switch_spdt", "switch_sp3t", "switch_dpdt"):
                menu.add_separator()
                menu.add_command(label=self.tr("menu_cycle"), command=lambda: self._click_component(comp))
            if comp.ctype == "button_momentary":
                menu.add_separator()
                menu.add_command(label=self.tr("press"), command=lambda: self.set_momentary(comp, 1))
                menu.add_command(label=self.tr("release"), command=lambda: self.set_momentary(comp, 0))

            if comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
                rngs = meter_ranges(comp)
                if rngs:
                    menu.add_separator()
                    sub = tk.Menu(menu, tearoff=0)
                    unit = "V" if comp.ctype == "voltmeter" else "A"
                    for i, r in enumerate(rngs):
                        sub.add_command(
                            label=f"{i}: {self.fmt(float(r), unit)}",
                            command=lambda idx=i: self._set_meter_range(comp, idx),
                        )
                    menu.add_cascade(label=self.tr("range"), menu=sub)
            menu.post(event.x_root, event.y_root)

    def _set_meter_range(self, comp: Component, idx: int):
        if self._is_locked(comp):
            return
        comp.props["range"] = int(idx)
        self.solve()
        self._record_history()
        self.redraw()

    def _toggle_lock(self, comp: Component, locked: bool):
        comp.meta["locked"] = "1" if locked else "0"
        self.redraw()

    def _duplicate_component(self, comp: Component):
        dx, dy = 2, 2
        a2 = (comp.a[0] + dx, comp.a[1] + dy)
        b2 = (comp.b[0] + dx, comp.b[1] + dy)
        props = dict(comp.props)
        props.pop("pressed", None)
        cid = self.cir.add(comp.ctype, a2, b2, **props)
        try:
            self.cir.components[cid].meta = dict(comp.meta)
            self.cir.components[cid].meta["locked"] = "0"
        except Exception:
            pass
        self.solve()
        self._record_history()
        self.redraw()

    def on_canvas_motion(self, event):
        grid_pos = self.grid_snap(event.x, event.y)
        if grid_pos == self._last_motion_grid:
            return
        self._last_motion_grid = grid_pos
        self._pending_motion_grid = grid_pos
        if self._hover_after_id is None:
            self._hover_after_id = self.root.after(30, self._apply_hover)

    def _apply_hover(self):
        self._hover_after_id = None
        if self._pending_motion_grid is None:
            return
        comp = self.cir.find_near(self._pending_motion_grid)
        if comp != self.hover_comp:
            self.hover_comp = comp
        if self.mode == "wire" and self.wire_start is not None:
            self._wire_preview_end = self._pending_motion_grid
        self.redraw()

    def on_canvas_double_click(self, event):
        grid_pos = self.grid_snap(event.x, event.y)
        comp = self.cir.find_near(grid_pos)
        if comp:
            self.edit_component(comp)

    def place_component(self, pos: Point):
        x, y = pos
        a = pos
        
        if self.place_type == "socket":
            b = (x, y + 6)
            self.cir.add("socket", a, b, V=float(self.defaults.get("socket_V", 5.0)), Iwarn=float(self.defaults.get("socket_Iwarn", 5.0)))
        elif self.place_type == "wire":
            b = (x + 8, y)
            self.cir.add("wire", a, b)
        elif self.place_type == "resistor":
            b = (x + 8, y)
            self.cir.add("resistor", a, b, R=float(self.defaults.get("resistor_R", 100.0)))
        elif self.place_type == "bulb":
            b = (x + 8, y)
            self.cir.add("bulb", a, b, Vr=6.0, Wr=3.0)
        elif self.place_type == "rheostat":
            b = (x + 8, y)
            self.cir.add(
                "rheostat",
                a,
                b,
                R=float(self.defaults.get("rheostat_R", 200.0)),
                Rmin=float(self.defaults.get("rheostat_Rmin", 0.0)),
                Rmax=float(self.defaults.get("rheostat_Rmax", 500.0)),
            )
        elif self.place_type == "switch_spst":
            b = (x + 6, y)
            self.cir.add("switch_spst", a, b, state=1)
        elif self.place_type == "switch_spdt":
            b = (x + 6, y)
            self.cir.add("switch_spdt", a, b, throw=0, c_x=b[0], c_y=y+4)
        elif self.place_type == "switch_sp3t":
            b = (x + 6, y)
            self.cir.add("switch_sp3t", a, b, throw=0, c_x=b[0], c_y=y+4, d_x=b[0], d_y=y+8)
        elif self.place_type == "switch_dpst":
            b = (x + 6, y)
            self.cir.add("switch_dpst", a, b, state=1, c_x=x, c_y=y+4, d_x=x+6, d_y=y+4)
        elif self.place_type == "switch_dpdt":
            b = (x + 6, y)
            self.cir.add(
                "switch_dpdt",
                a,
                b,
                throw=0,
                c_x=b[0], c_y=y+2,
                d_x=x, d_y=y+6,
                e_x=x+6, e_y=y+6,
                f_x=x+6, f_y=y+8,
            )
        elif self.place_type == "button_momentary":
            b = (x + 6, y)
            self.cir.add("button_momentary", a, b, pressed=0)
        elif self.place_type == "ammeter":
            b = (x + 6, y)
            cid = self.cir.add("ammeter", a, b, burden_V=float(self.defaults.get("ammeter_burden_V", 0.05)), range=0)
            self.cir.components[cid].meta["ranges_I"] = "[0.01, 0.1, 1]"
        elif self.place_type == "voltmeter":
            b = (x + 6, y)
            cid = self.cir.add("voltmeter", a, b, ohm_per_V=float(self.defaults.get("voltmeter_ohm_per_V", 20000.0)), range=1)
            self.cir.components[cid].meta["ranges_V"] = "[0.3, 3, 30]"
        elif self.place_type == "galvanometer":
            b = (x + 6, y)
            cid = self.cir.add(
                "galvanometer",
                a,
                b,
                Rcoil=float(self.defaults.get("galv_Rcoil", 50.0)),
                Ifs=float(self.defaults.get("galv_Ifs", 50e-6)),
                range=0,
            )
            self.cir.components[cid].meta["ranges_I"] = "[5e-5, 5e-4, 5e-3]"
        
        self.solve()
        self._record_history()
        self.redraw()
        self.status_label.config(text=self.tr("placed", ctype=self._tr_comp(self.place_type), pos=pos))

    def toggle_wire(self, pos: Point):
        if self.wire_start is None:
            self.wire_start = pos
            self._wire_preview_end = pos
            self.status_label.config(text=self.tr("wire_start", pos=pos))
        else:
            self.cir.add("wire", self.wire_start, pos)
            self.status_label.config(text=self.tr("wire_added", a=self.wire_start, b=pos))
            self.wire_start = None
            self._wire_preview_end = None
            self.mode = "navigate"
            self.mode_label.config(text=self.tr("mode_navigate"))
            self.solve()
            self._record_history()
            self.redraw()

    def delete_component(self, comp: Component):
        if comp.cid in self.cir.components:
            del self.cir.components[comp.cid]
            self.selected_comp = None
            self.hover_comp = None
            self.solve()
            self._record_history()
            self.redraw()
            self.status_label.config(text=self.tr("deleted", name=comp.display_name()))

    def toggle_switch(self, comp: Component):
        if comp.ctype == "switch_spst":
            state = int(comp.props.get("state", 1))
            comp.props["state"] = 0 if state == 1 else 1
            self.solve()
            self._record_history()
            self.redraw()
            self.status_label.config(text=self.tr("switch_opened") if comp.props["state"] == 0 else self.tr("switch_closed"))

    def set_momentary(self, comp: Component, pressed: int):
        if comp.ctype != "button_momentary":
            return
        comp.props["pressed"] = 1 if pressed else 0
        self.solve()
        self._record_history()
        self.redraw()

    def edit_component(self, comp: Component):
        dialog = ComponentEditDialog(self.root, comp, tr=self.tr)
        if dialog.result:
            comp.props.update(dialog.result)
            self.solve()
            self._record_history()
            self.redraw()

    def solve(self):
        self.result = solve_circuit(self.cir)

    def solve_and_redraw(self):
        self.solve()
        self.redraw()
        if self.result.singular:
            self.status_label.config(text=self.tr("simulation_failed_singular"))
        else:
            self.status_label.config(text=self.tr("simulation_complete"))

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cir.to_json(), f, ensure_ascii=False, indent=2)
            self.status_label.config(text=self.tr("saved_to", path=SAVE_FILE))
        except Exception as e:
            messagebox.showerror(self.tr("save_error"), str(e))

    def load(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.cir = Circuit.from_json(obj)
            self.history.clear()
            self.history.record(self.cir)
            self.solve()
            self.redraw()
            self.status_label.config(text=self.tr("loaded_from", path=SAVE_FILE))
        except Exception as e:
            messagebox.showerror(self.tr("load_error"), str(e))

    def clear_all(self):
        if messagebox.askyesno(self.tr("clear_all_confirm_title"), self.tr("clear_all_confirm_msg")):
            self.cir = Circuit()
            self.selected_comp = None
            self.hover_comp = None
            self.history.clear()
            self.history.record(self.cir)
            self.solve()
            self.redraw()
            self.status_label.config(text=self.tr("circuit_cleared"))

    def redraw(self):
        self.canvas.delete("all")
        
        for y in range(0, CANVAS_H, GRID_SIZE):
            self.canvas.create_line(0, y, CANVAS_W, y, fill="#e0e0e0", width=1)
        for x in range(0, CANVAS_W, GRID_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_H, fill="#e0e0e0", width=1)
        
        for y in range(0, CANVAS_H, GRID_SIZE * 2):
            for x in range(0, CANVAS_W, GRID_SIZE * 2):
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="#d0d0d0", outline="")
        
        for comp in self.cir.components.values():
            self.draw_component(comp)
        
        if self.wire_start:
            x, y = self.grid_to_canvas(self.wire_start)
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue", outline="darkblue", width=2)

        if self.wire_start and self._wire_preview_end and self.mode == "wire":
            x1, y1 = self.grid_to_canvas(self.wire_start)
            x2, y2 = self.grid_to_canvas(self._wire_preview_end)
            self.canvas.create_line(x1, y1, x2, y2, fill="#1e88e5", width=2, dash=(4, 4))
        
        self.update_info_panel()
        self.refresh_inspector()

    def draw_component(self, comp: Component):
        x1, y1 = self.grid_to_canvas(comp.a)
        x2, y2 = self.grid_to_canvas(comp.b)
        
        is_selected = (self.selected_comp and self.selected_comp.cid == comp.cid)
        is_hover = (self.hover_comp and self.hover_comp.cid == comp.cid)
        
        line_color = "red" if is_selected else "blue" if is_hover else "black"
        line_width = 3 if is_selected else 2
        
        flag = self.result.comp_flags.get(comp.cid)
        open_like = False
        if flag == "open":
            open_like = True
        if comp.ctype == "switch_spst" and int(comp.props.get("state", 1)) == 0:
            open_like = True
        if comp.ctype == "button_momentary" and int(comp.props.get("pressed", 0)) == 0:
            open_like = True

        if open_like:
            line_color = "gray"
            mx = (x1 + x2) // 2
            my = (y1 + y2) // 2
            self.canvas.create_line(x1, y1, mx-6, my-6 if (x1 != x2 and y1 != y2) else my, fill=line_color, width=line_width, dash=(6, 6))
            self.canvas.create_line(mx+6, my+6 if (x1 != x2 and y1 != y2) else my, x2, y2, fill=line_color, width=line_width, dash=(6, 6))
        else:
            if flag == "overcurrent":
                line_color = "#d32f2f"
                line_width = max(line_width, 3)
            self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)
        
        self.canvas.create_oval(x1-4, y1-4, x1+4, y1+4, fill="darkgreen", outline="")
        self.canvas.create_oval(x2-4, y2-4, x2+4, y2+4, fill="darkgreen", outline="")
        
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2
        
        symbol = comp_symbol(comp)
        bg_color = "yellow" if is_selected else "lightblue" if is_hover else "white"
        if self._is_locked(comp):
            bg_color = "#f5f5f5"
        
        if comp.ctype == "socket":
            outline = "red" if flag == "source_overcurrent" else "black"
            self.canvas.create_rectangle(mx-15, my-15, mx+15, my+15, fill=bg_color, outline=outline, width=2)
            self.canvas.create_text(mx, my, text=symbol, font=("Arial", 16, "bold"))
            if is_selected or is_hover:
                Vmin = float(self.defaults.get("socket_Vmin", 0.0))
                Vmax = float(self.defaults.get("socket_Vmax", 12.0))
                if Vmax < Vmin:
                    Vmin, Vmax = Vmax, Vmin
                V = float(comp.props.get("V", self.defaults.get("socket_V", 5.0)))
                t = 0.0
                if abs(Vmax - Vmin) > 1e-12:
                    t = (V - Vmin) / (Vmax - Vmin)
                if t < 0.0:
                    t = 0.0
                if t > 1.0:
                    t = 1.0
                x0, y0 = mx - 18, my + 22
                x1, y1 = mx + 18, my + 22
                self.canvas.create_line(x0, y0, x1, y1, fill="#777", width=2)
                kx = int(x0 + t * (x1 - x0))
                self.canvas.create_oval(kx-4, y0-4, kx+4, y0+4, fill="#1e88e5", outline="")
                self.canvas.create_text(mx, my + 34, text=self.fmt(V, "V"), font=("Arial", 8), fill="#444")
        elif comp.ctype == "bulb":
            Va = self.result.node_v.get(comp.a, 0.0)
            Vb = self.result.node_v.get(comp.b, 0.0)
            Vab = abs(Va - Vb)
            Vr = float(comp.props.get("Vr", 6.0))
            brightness = min(Vab / Vr, 1.0) if Vr > 0 else 0
            
            if brightness > 0.7:
                bulb_color = "yellow"
            elif brightness > 0.3:
                bulb_color = "orange"
            else:
                bulb_color = "gray"
            
            self.canvas.create_oval(mx-12, my-12, mx+12, my+12, fill=bulb_color, outline="black", width=2)
            self.canvas.create_text(mx, my, text="💡", font=("Arial", 14))
        elif comp.ctype == "resistor":
            self.canvas.create_rectangle(mx-20, my-8, mx+20, my+8, fill=bg_color, outline="black", width=2)
            self.canvas.create_text(mx, my, text=symbol, font=("Arial", 14, "bold"))
            if is_selected or is_hover:
                Rmin = float(self.defaults.get("resistor_Rmin", 1.0))
                Rmax = float(self.defaults.get("resistor_Rmax", 1e6))
                if Rmax < Rmin:
                    Rmin, Rmax = Rmax, Rmin
                if Rmin <= 0.0:
                    Rmin = 1e-6
                R = float(comp.props.get("R", self.defaults.get("resistor_R", 100.0)))
                t = 0.0
                if abs(math.log10(Rmax) - math.log10(Rmin)) > 1e-12 and R > 0:
                    t = (math.log10(R) - math.log10(Rmin)) / (math.log10(Rmax) - math.log10(Rmin))
                if t < 0.0:
                    t = 0.0
                if t > 1.0:
                    t = 1.0
                x0, y0 = mx - 22, my + 18
                x1, y1 = mx + 22, my + 18
                self.canvas.create_line(x0, y0, x1, y1, fill="#777", width=2)
                kx = int(x0 + t * (x1 - x0))
                self.canvas.create_oval(kx-4, y0-4, kx+4, y0+4, fill="#1e88e5", outline="")
                self.canvas.create_text(mx, my + 30, text=self.fmt(R, "Ω"), font=("Arial", 8), fill="#444")
        elif comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
            self.canvas.create_oval(mx-12, my-12, mx+12, my+12, fill=bg_color, outline="black", width=2)
            self.canvas.create_arc(mx-14, my-14, mx+14, my+14, start=120, extent=300, style=tk.ARC, outline="#666", width=1)
            fsd = meter_native_full_scale(comp)
            unit = "V" if comp.ctype == "voltmeter" else "A"
            for i in range(0, 21):
                t = i / 20.0
                ang = (-120.0 + 240.0 * t) * math.pi / 180.0
                major = (i % 5) == 0
                r0 = 9 if major else 11
                r1 = 14
                x0 = mx + int(r0 * math.cos(ang))
                y0 = my + int(r0 * math.sin(ang))
                x1t = mx + int(r1 * math.cos(ang))
                y1t = my + int(r1 * math.sin(ang))
                self.canvas.create_line(x0, y0, x1t, y1t, fill="#555", width=2 if major else 1)
                if major:
                    if fsd is None:
                        lab = "0" if i == 0 else "" 
                    else:
                        lab = self.fmt(0.0, unit) if i == 0 else self.fmt(float(fsd) / 2.0, unit) if i == 10 else self.fmt(float(fsd), unit) if i == 20 else ""
                    if lab:
                        xr = mx + int(17 * math.cos(ang))
                        yr = my + int(17 * math.sin(ang))
                        self.canvas.create_text(xr, yr, text=lab, font=("Arial", 7), fill="#444")
            self.canvas.create_text(mx, my + 1, text=symbol, font=("Arial", 12, "bold"))
        elif comp.ctype == "rheostat":
            self.canvas.create_oval(mx-10, my-10, mx+10, my+10, fill=bg_color, outline="black", width=2)
            self.canvas.create_text(mx, my, text=symbol, font=("Arial", 12, "bold"))
            Rmin = float(comp.props.get("Rmin", self.defaults.get("rheostat_Rmin", 0.0)))
            Rmax = float(comp.props.get("Rmax", self.defaults.get("rheostat_Rmax", 500.0)))
            if Rmax < Rmin:
                Rmin, Rmax = Rmax, Rmin
            R = float(comp.props.get("R", self.defaults.get("rheostat_R", 200.0)))
            t = 0.0
            if abs(Rmax - Rmin) > 1e-12:
                t = (R - Rmin) / (Rmax - Rmin)
            if t < 0.0:
                t = 0.0
            if t > 1.0:
                t = 1.0
            horizontal = abs(x2 - x1) >= abs(y2 - y1)
            if horizontal:
                sx0, sy0 = mx - 12, my + 14
                sx1, sy1 = mx + 12, my + 14
                kx = int(sx0 + t * (sx1 - sx0))
                ky = sy0
            else:
                sx0, sy0 = mx + 14, my - 12
                sx1, sy1 = mx + 14, my + 12
                kx = sx0
                ky = int(sy0 + t * (sy1 - sy0))
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill="#777", width=2)
            self.canvas.create_oval(kx-4, ky-4, kx+4, ky+4, fill="#1e88e5", outline="")
        else:
            self.canvas.create_oval(mx-10, my-10, mx+10, my+10, fill=bg_color, outline="black", width=2)
            self.canvas.create_text(mx, my, text=symbol, font=("Arial", 12, "bold"))
        
        if self.result.ok and comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
            Va = self.result.node_v.get(comp.a, 0.0)
            Vb = self.result.node_v.get(comp.b, 0.0)
            Iab = self.result.comp_i.get(comp.cid, 0.0)
            
            if comp.ctype == "voltmeter":
                val = Va - Vb
                fs = meter_native_full_scale(comp)
                ol = (fs is not None and abs(val) > abs(fs) * 1.02)
                reading = self.tr("ol") if ol else self.fmt(val, "V")
            else:
                val = Iab
                fs = meter_native_full_scale(comp)
                ol = (fs is not None and abs(val) > abs(fs) * 1.02)
                reading = self.tr("ol") if ol else self.fmt(val, "A")

            if ol:
                self.canvas.create_arc(mx-14, my-14, mx+14, my+14, start=120, extent=300, style=tk.ARC, outline="#d32f2f", width=2)

            ratio = 0.0
            if fs is not None and abs(fs) > 1e-15:
                ratio = abs(val) / abs(fs)
            if ol:
                ratio = 1.1
            if ratio < 0.0:
                ratio = 0.0
            if ratio > 1.1:
                ratio = 1.1
            ang0 = -120.0
            ang1 = 120.0
            ang = (ang0 + (ang1 - ang0) * min(ratio, 1.0)) * math.pi / 180.0
            r = 12
            xN = mx + int(r * math.cos(ang))
            yN = my + int(r * math.sin(ang))
            self.canvas.create_line(mx, my, xN, yN, fill="#d32f2f", width=2)
            self.canvas.create_oval(mx-2, my-2, mx+2, my+2, fill="#d32f2f", outline="")

            if fs is not None:
                unit = "V" if comp.ctype == "voltmeter" else "A"
                self.canvas.create_text(mx, my - 16, text=self.fmt(fs, unit), font=("Arial", 7), fill="#444")
            
            self.canvas.create_text(mx, my + 20, text=reading, font=("Arial", 9), fill="darkred")

        if getattr(self, "_opt_show_labels", True):
            self._draw_canvas_value_label(comp, mx, my)

    def _draw_canvas_value_label(self, comp: Component, mx: int, my: int):
        if not (self.selected_comp and self.selected_comp.cid == comp.cid) and not (self.hover_comp and self.hover_comp.cid == comp.cid):
            return
        lines: List[str] = []
        if comp.ctype == "socket":
            try:
                V = float(comp.props.get("V", self.defaults.get("socket_V", 5.0)))
                lines.append(f"V={self.fmt(V, 'V')}")
            except Exception:
                pass
        if comp.ctype == "resistor":
            try:
                R = float(comp.props.get("R", self.defaults.get("resistor_R", 100.0)))
                lines.append(f"R={self.fmt(R, 'Ω')}")
            except Exception:
                pass
        if comp.ctype == "rheostat":
            try:
                R = float(comp.props.get("R", self.defaults.get("rheostat_R", 200.0)))
                lines.append(f"R={self.fmt(R, 'Ω')}")
            except Exception:
                pass
        if comp.ctype in ("ammeter", "galvanometer") and self.result.ok:
            Iab = self.result.comp_i.get(comp.cid, 0.0)
            fs = meter_native_full_scale(comp)
            ol = (fs is not None and abs(Iab) > abs(fs) * 1.02)
            lines.append((self.tr("ol") if ol else self.fmt(Iab, "A")))
        if comp.ctype == "voltmeter" and self.result.ok:
            Va = self.result.node_v.get(comp.a, 0.0)
            Vb = self.result.node_v.get(comp.b, 0.0)
            Vab = Va - Vb
            fs = meter_native_full_scale(comp)
            ol = (fs is not None and abs(Vab) > abs(fs) * 1.02)
            lines.append((self.tr("ol") if ol else self.fmt(Vab, "V")))
        if not lines:
            return
        text = "\n".join(lines)
        x = mx + 18
        y = my - 18
        tid = self.canvas.create_text(x, y, text=text, font=("Arial", 9, "bold"), fill="#111", anchor="nw")
        bb = self.canvas.bbox(tid)
        if bb:
            pad = 3
            self.canvas.create_rectangle(bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad, fill="#ffffff", outline="#c8c8c8")
            self.canvas.tag_raise(tid)

    def update_info_panel(self):
        cards = getattr(self, "_status_cards", {})
        if not cards:
            return

        comp_sel = self.selected_comp
        comp_hover = self.hover_comp
        comp = comp_sel or comp_hover

        sel_lines: List[str] = []
        if comp_sel:
            sel_lines.append(f"{self.tr('selected')}: {comp_sel.display_name()}")
            sel_lines.append(f"{self.tr('info_type')}: {self._tr_comp(comp_sel.ctype)}")
            if self._is_locked(comp_sel):
                sel_lines.append(f"{self.tr('locked')}")
        else:
            sel_lines.append(f"{self.tr('selected')}: {self.tr('none')}")
        if comp_hover and (not comp_sel or comp_hover.cid != comp_sel.cid):
            sel_lines.append(f"{self.tr('hovered')}: {comp_hover.display_name()}")
        if comp:
            sel_lines.append(f"{self.tr('info_endpoints')}: a={comp.a}  b={comp.b}")
        cards["sel"]["value"].config(text="\n".join(sel_lines))

        if comp and self.result.ok:
            Va = self.result.node_v.get(comp.a, 0.0)
            Vb = self.result.node_v.get(comp.b, 0.0)
            Iab = self.result.comp_i.get(comp.cid, 0.0)
            Vab = Va - Vb
            P = Vab * Iab

            meas_lines: List[str] = []
            if comp.ctype in ("ammeter", "galvanometer"):
                fs = meter_native_full_scale(comp)
                reading = self.tr("ol") if (fs is not None and abs(Iab) > abs(fs) * 1.02) else self.fmt(Iab, "A")
                meas_lines.append(f"{self.tr('info_current')}: {reading}")
            elif comp.ctype == "voltmeter":
                fs = meter_native_full_scale(comp)
                reading = self.tr("ol") if (fs is not None and abs(Vab) > abs(fs) * 1.02) else self.fmt(Vab, "V")
                meas_lines.append(f"{self.tr('info_voltage')}: {reading}")
            else:
                meas_lines.append(f"{self.tr('info_voltage')}: {self.fmt(Vab, 'V')}")
                meas_lines.append(f"{self.tr('info_current')}: {self.fmt(Iab, 'A')}")
            meas_lines.append(f"{self.tr('info_power')}: {self.fmt(P, 'W')}")
            if comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
                fs = meter_full_scale(comp)
                if fs is not None:
                    unit = "V" if comp.ctype == "voltmeter" else "A"
                    meas_lines.append(f"{self.tr('range')}: {self.fmt(fs, unit)}")
            cards["meas"]["value"].config(text="\n".join(meas_lines))
        else:
            cards["meas"]["value"].config(text=self.tr("hover_hint"))

        stat_lines: List[str] = []
        stat_lines.append(f"{self.tr('info_status')}: {self.tr('solve_failed') if (self.result.singular or not self.result.ok) else self.tr('solve_ok')}")
        if comp:
            fl = self._flag_text(self.result.comp_flags.get(comp.cid))
            if fl:
                stat_lines.append(f"{fl}")
        if self.result.warnings:
            stat_lines.append(f"{self.tr('warnings')}: {len(self.result.warnings)}")
        cards["stat"]["value"].config(text="\n".join(stat_lines))

        self._opt_show_shortcuts = bool(getattr(self, "_opt_show_shortcuts", True))
        if self._opt_show_shortcuts:
            cards["keys"]["frame"].grid()
            cards["keys"]["value"].config(text="\n".join([
                "Ctrl/Cmd+Z: " + self.tr("undo"),
                "Ctrl/Cmd+Y: " + self.tr("redo"),
                "G: " + self.tr("goal_seek"),
                "W/N: " + self.tr("wire_tool") + "/" + self.tr("navigate"),
                "Wheel@Rheo: ΔR (Shift x10)",
                "Wheel@Src/Res/Meter: adjust",
            ]))
        else:
            try:
                cards["keys"]["frame"].grid_remove()
            except Exception:
                pass

        self._style_status_cards(cards, comp)

    def _style_status_cards(self, cards: Dict[str, Any], comp: Optional[Component]):
        ok = (self.result.ok and not self.result.singular)
        warn = bool(self.result.warnings)
        if not ok:
            bg = "#ffebee"; fg = "#b71c1c"; icon = "⛔ "
        elif warn:
            bg = "#fff8e1"; fg = "#e65100"; icon = "⚠ "
        else:
            bg = "#e8f5e9"; fg = "#1b5e20"; icon = "✅ "
        try:
            cards["stat"]["frame"].config(bg=bg)
            cards["stat"]["title"].config(bg=bg, fg=fg, text=icon + self.tr(cards["stat"].get("title_key", "panel_status")))
            cards["stat"]["value"].config(bg=bg, fg="#222")
        except Exception:
            pass
        try:
            for k in ("sel", "meas", "keys"):
                cards[k]["title"].config(text=self.tr(cards[k].get("title_key", "")))
        except Exception:
            pass

    def _build_options(self, parent):
        w = self._i18n_widgets

        self._var_fmt = tk.StringVar(value=str(self._fmt_style or "si"))
        self._var_sig = tk.IntVar(value=int(self._fmt_sig))
        self._var_max = tk.StringVar(value=str(self._fmt_max_abs))
        self._var_min = tk.StringVar(value=str(self._fmt_min_abs))
        self._var_show_shortcuts = tk.IntVar(value=1 if self._opt_show_shortcuts else 0)
        self._var_show_labels = tk.IntVar(value=1 if self._opt_show_labels else 0)

        self._var_def_source_v = tk.StringVar(value=str(self.defaults.get("socket_V", 5.0)))
        self._var_def_source_iwarn = tk.StringVar(value=str(self.defaults.get("socket_Iwarn", 5.0)))
        self._var_def_res_r = tk.StringVar(value=str(self.defaults.get("resistor_R", 100.0)))
        self._var_def_rheo_r = tk.StringVar(value=str(self.defaults.get("rheostat_R", 200.0)))
        self._var_def_rheo_min = tk.StringVar(value=str(self.defaults.get("rheostat_Rmin", 0.0)))
        self._var_def_rheo_max = tk.StringVar(value=str(self.defaults.get("rheostat_Rmax", 500.0)))
        self._var_def_amm_burden = tk.StringVar(value=str(self.defaults.get("ammeter_burden_V", 0.05)))
        self._var_def_volt_sens = tk.StringVar(value=str(self.defaults.get("voltmeter_ohm_per_V", 20000.0)))
        self._var_def_gal_r = tk.StringVar(value=str(self.defaults.get("galv_Rcoil", 50.0)))
        self._var_def_gal_ifs = tk.StringVar(value=str(self.defaults.get("galv_Ifs", 50e-6)))

        frm = ttk.Frame(parent)
        frm.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        def mk_label(text_key: str):
            lbl = ttk.Label(frm, text=self.tr(text_key))
            lbl.i18n_key = text_key
            return lbl

        row = 0
        lbl = mk_label("opt_format"); lbl.grid(row=row, column=0, sticky=tk.W, pady=2); w["lbl_opt_format"] = lbl
        cb = ttk.Combobox(frm, state="readonly", width=12)
        cb.config(values=[self.tr("opt_fmt_si"), self.tr("opt_fmt_sci")])
        cb.current(0 if str(self._fmt_style) != "sci" else 1)
        w["cb_opt_format"] = cb

        def on_fmt(_e):
            self._var_fmt.set("si" if cb.current() == 0 else "sci")

        cb.bind("<<ComboboxSelected>>", on_fmt)
        cb.grid(row=row, column=1, sticky=tk.EW, pady=2)

        row += 1
        lbl = mk_label("opt_sig"); lbl.grid(row=row, column=0, sticky=tk.W, pady=2); w["lbl_opt_sig"] = lbl
        sp = ttk.Spinbox(frm, from_=2, to=8, textvariable=self._var_sig, width=8)
        sp.grid(row=row, column=1, sticky=tk.W, pady=2)

        row += 1
        lbl = mk_label("opt_max_abs"); lbl.grid(row=row, column=0, sticky=tk.W, pady=2); w["lbl_opt_max"] = lbl
        ttk.Entry(frm, textvariable=self._var_max, width=12).grid(row=row, column=1, sticky=tk.W, pady=2)

        row += 1
        lbl = mk_label("opt_min_abs"); lbl.grid(row=row, column=0, sticky=tk.W, pady=2); w["lbl_opt_min"] = lbl
        ttk.Entry(frm, textvariable=self._var_min, width=12).grid(row=row, column=1, sticky=tk.W, pady=2)

        row += 1
        chk = ttk.Checkbutton(frm, text=self.tr("opt_show_shortcuts"), variable=self._var_show_shortcuts)
        chk.i18n_key = "opt_show_shortcuts"
        chk.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(4, 8))
        w["chk_show_shortcuts"] = chk

        row += 1
        chk2 = ttk.Checkbutton(frm, text=self.tr("opt_show_labels"), variable=self._var_show_labels)
        chk2.i18n_key = "opt_show_labels"
        chk2.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        w["chk_show_labels"] = chk2

        row += 1
        sep = ttk.Separator(frm, orient=tk.HORIZONTAL)
        sep.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=6)

        row += 1
        lbl = mk_label("opt_defaults"); lbl.grid(row=row, column=0, sticky=tk.W, pady=2); w["lbl_opt_defaults"] = lbl

        def mk_kv(r, widget_key: str, i18n_key: str, var):
            lab = mk_label(i18n_key)
            lab.grid(row=r, column=0, sticky=tk.W, pady=1)
            w[f"lbl_{widget_key}"] = lab
            ttk.Entry(frm, textvariable=var, width=12).grid(row=r, column=1, sticky=tk.W, pady=1)

        row += 1
        mk_kv(row, "def_source_v", "opt_def_source_v", self._var_def_source_v)
        row += 1
        mk_kv(row, "def_source_iwarn", "opt_def_source_iwarn", self._var_def_source_iwarn)
        row += 1
        mk_kv(row, "def_res_r", "opt_def_res_r", self._var_def_res_r)
        row += 1
        mk_kv(row, "def_rheo_r", "opt_def_rheo_r", self._var_def_rheo_r)
        row += 1
        mk_kv(row, "def_rheo_min", "opt_def_rheo_min", self._var_def_rheo_min)
        row += 1
        mk_kv(row, "def_rheo_max", "opt_def_rheo_max", self._var_def_rheo_max)
        row += 1
        mk_kv(row, "def_amm_burden", "opt_def_amm_burden", self._var_def_amm_burden)
        row += 1
        mk_kv(row, "def_volt_sens", "opt_def_volt_sens", self._var_def_volt_sens)
        row += 1
        mk_kv(row, "def_gal_r", "opt_def_gal_r", self._var_def_gal_r)
        row += 1
        mk_kv(row, "def_gal_ifs", "opt_def_gal_ifs", self._var_def_gal_ifs)

        row += 1
        btn = ttk.Button(frm, text=self.tr("apply"), command=self._apply_options)
        btn.i18n_key = "apply"
        btn.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=(10, 2))
        w["btn_opt_apply"] = btn

        frm.columnconfigure(1, weight=1)

    def _apply_options(self):
        try:
            self._fmt_style = str(self._var_fmt.get() or "si")
        except Exception:
            self._fmt_style = "si"
        try:
            self._fmt_sig = int(self._var_sig.get())
        except Exception:
            pass
        try:
            self._fmt_max_abs = float(self._var_max.get())
        except Exception:
            pass
        try:
            self._fmt_min_abs = float(self._var_min.get())
        except Exception:
            pass

        try:
            self._opt_show_shortcuts = bool(int(self._var_show_shortcuts.get()))
        except Exception:
            self._opt_show_shortcuts = True
        try:
            self._opt_show_labels = bool(int(self._var_show_labels.get()))
        except Exception:
            self._opt_show_labels = True

        def setd(key, var):
            try:
                self.defaults[key] = float(var.get())
            except Exception:
                pass

        setd("socket_V", self._var_def_source_v)
        setd("socket_Iwarn", self._var_def_source_iwarn)
        setd("resistor_R", self._var_def_res_r)
        setd("rheostat_R", self._var_def_rheo_r)
        setd("rheostat_Rmin", self._var_def_rheo_min)
        setd("rheostat_Rmax", self._var_def_rheo_max)
        setd("ammeter_burden_V", self._var_def_amm_burden)
        setd("voltmeter_ohm_per_V", self._var_def_volt_sens)
        setd("galv_Rcoil", self._var_def_gal_r)
        setd("galv_Ifs", self._var_def_gal_ifs)

        self.redraw()

class ComponentEditDialog:
    def __init__(self, parent, comp: Component, tr=None):
        self.result = None
        self.comp = comp
        self.tr = tr
        
        self.dialog = tk.Toplevel(parent)
        if callable(self.tr):
            self.dialog.title(self.tr("edit_title", name=comp.display_name()))
        else:
            self.dialog.title(f"Edit {comp.display_name()}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        hdr = f"Edit Properties: {comp.ctype}"
        if callable(self.tr):
            hdr = f"{self.tr('edit_properties')}: {comp.ctype}"
        ttk.Label(self.dialog, text=hdr, font=("Arial", 12, "bold")).pack(pady=10)
        
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.entries = {}
        fields = self.get_fields()
        
        for i, (key, label, default) in enumerate(fields):
            lbl = label
            if callable(self.tr):
                lbl = self.tr(label)
            ttk.Label(frame, text=lbl).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=20)
            entry.insert(0, str(comp.props.get(key, default)))
            entry.grid(row=i, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
            self.entries[key] = entry
        
        frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        ok_txt = "OK" if not callable(self.tr) else self.tr("ok")
        cancel_txt = "Cancel" if not callable(self.tr) else self.tr("cancel")
        ttk.Button(btn_frame, text=ok_txt, command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=cancel_txt, command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.wait_window()

    def get_fields(self):
        t = self.comp.ctype
        if t == "socket":
            return [("V", "prop_voltage", 5.0), ("Iwarn", "prop_current_warning", 5.0)]
        elif t == "resistor":
            return [("R", "prop_resistance", 100.0)]
        elif t == "bulb":
            return [("Vr", "prop_rated_voltage", 6.0), ("Wr", "prop_rated_power", 3.0)]
        elif t == "rheostat":
            return [("R", "prop_resistance", 100.0)]
        elif t == "switch_spst":
            return [("state", "prop_state", 1)]
        elif t == "switch_spdt":
            return [("throw", "prop_throw", 0)]
        elif t == "ammeter":
            return [("Rin", "prop_internal_resistance", 0.05)]
        elif t == "voltmeter":
            return [("Rin", "prop_internal_resistance", 1e6)]
        elif t == "galvanometer":
            return [("Rcoil", "prop_coil_resistance", 50.0), ("Ifs", "prop_full_scale_current", 50e-6)]
        return []

    def ok(self):
        self.result = {}
        for key, entry in self.entries.items():
            try:
                self.result[key] = float(entry.get())
            except ValueError:
                title = "Invalid Input"
                if callable(self.tr):
                    title = self.tr("invalid_input")
                messagebox.showerror(title, f"Invalid value for {key}")
                return
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()


class GoalSeekDialog:
    def __init__(self, parent, cir: Circuit, selected: Optional[Component], tr=None, tr_comp=None):
        self.result: Optional[Dict[str, Any]] = None
        self.cir = cir
        self.tr = tr
        self.tr_comp = tr_comp

        def _t(key: str, **kwargs) -> str:
            if callable(self.tr):
                return self.tr(key, **kwargs)
            return key

        def _tc(ctype: str) -> str:
            if callable(self.tr_comp):
                return self.tr_comp(ctype)
            return ctype

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(_t("gs_dialog_title"))
        self.dialog.geometry("520x440")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text=_t("gs_dialog_header"), font=("Arial", 12, "bold")).pack(pady=8)

        body = ttk.Frame(self.dialog)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        allowed_var = ("resistor", "rheostat", "socket")
        self._var_items: List[str] = []
        self._var_map: Dict[str, str] = {}
        for c in self.cir.components.values():
            if c.ctype in allowed_var:
                label = f"{c.cid[:6]} {_tc(c.ctype)}"
                self._var_items.append(label)
                self._var_map[label] = c.cid
        self._var_items.sort()

        self._meas_items: List[str] = []
        self._meas_map: Dict[str, str] = {}
        for c in self.cir.components.values():
            label = f"{c.cid[:6]} {_tc(c.ctype)}"
            self._meas_items.append(label)
            self._meas_map[label] = c.cid
        self._meas_items.sort()

        row = 0
        ttk.Label(body, text=_t("gs_variable_component")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.var_comp = ttk.Combobox(body, values=self._var_items, state="readonly")
        self.var_comp.grid(row=row, column=1, sticky=tk.EW, pady=4)

        row += 1
        ttk.Label(body, text=_t("gs_variable_prop")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.var_prop = ttk.Combobox(body, values=["R", "V"], state="readonly")
        self.var_prop.grid(row=row, column=1, sticky=tk.W, pady=4)

        row += 1
        ttk.Separator(body, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=8)

        row += 1
        ttk.Label(body, text=_t("gs_measure")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.measure_kind = tk.StringVar(value="comp")
        mf = ttk.Frame(body)
        mf.grid(row=row, column=1, sticky=tk.W)
        ttk.Radiobutton(mf, text=_t("gs_component"), variable=self.measure_kind, value="comp", command=self._sync_measure_visibility).pack(side=tk.LEFT)
        ttk.Radiobutton(mf, text=_t("gs_node"), variable=self.measure_kind, value="node", command=self._sync_measure_visibility).pack(side=tk.LEFT, padx=8)

        row += 1
        ttk.Label(body, text=_t("gs_measure_component")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.meas_comp = ttk.Combobox(body, values=self._meas_items, state="readonly")
        self.meas_comp.grid(row=row, column=1, sticky=tk.EW, pady=4)

        row += 1
        ttk.Label(body, text=_t("gs_field")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.meas_field = ttk.Combobox(body, values=["Iab", "Vab", "Va", "Vb", "P", "R"], state="readonly")
        self.meas_field.grid(row=row, column=1, sticky=tk.W, pady=4)

        row += 1
        ttk.Label(body, text=_t("gs_branch_optional")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.meas_branch = ttk.Entry(body)
        self.meas_branch.grid(row=row, column=1, sticky=tk.EW, pady=4)

        row += 1
        self.meas_abs = tk.IntVar(value=1)
        ttk.Checkbutton(body, text=_t("gs_abs_value"), variable=self.meas_abs).grid(row=row, column=1, sticky=tk.W, pady=4)

        row += 1
        self.node_frame = ttk.Frame(body)
        ttk.Label(body, text=_t("gs_node_xy")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.node_frame.grid(row=row, column=1, sticky=tk.W, pady=4)
        self.node_x = ttk.Entry(self.node_frame, width=6)
        self.node_y = ttk.Entry(self.node_frame, width=6)
        self.node_x.pack(side=tk.LEFT)
        ttk.Label(self.node_frame, text=",").pack(side=tk.LEFT, padx=2)
        self.node_y.pack(side=tk.LEFT)
        self.node_abs = tk.IntVar(value=0)
        ttk.Checkbutton(self.node_frame, text=_t("gs_abs"), variable=self.node_abs).pack(side=tk.LEFT, padx=10)

        row += 1
        ttk.Separator(body, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=8)

        row += 1
        ttk.Label(body, text=_t("gs_target")).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.target = ttk.Entry(body)
        self.target.grid(row=row, column=1, sticky=tk.EW, pady=4)

        row += 1
        ttk.Label(body, text=_t("gs_lo_hi")).grid(row=row, column=0, sticky=tk.W, pady=4)
        bf = ttk.Frame(body)
        bf.grid(row=row, column=1, sticky=tk.W, pady=4)
        self.lo = ttk.Entry(bf, width=10)
        self.hi = ttk.Entry(bf, width=10)
        self.lo.pack(side=tk.LEFT)
        ttk.Label(bf, text=" .. ").pack(side=tk.LEFT)
        self.hi.pack(side=tk.LEFT)

        row += 1
        self.reject_overcurrent = tk.IntVar(value=0)
        ttk.Checkbutton(body, text=_t("gs_reject_overcurrent"), variable=self.reject_overcurrent).grid(row=row, column=1, sticky=tk.W, pady=6)

        row += 1
        self.auto_range = tk.IntVar(value=1)
        ttk.Checkbutton(body, text=_t("gs_auto_range"), variable=self.auto_range).grid(row=row, column=1, sticky=tk.W, pady=2)

        body.columnconfigure(1, weight=1)

        btns = ttk.Frame(self.dialog)
        btns.pack(pady=10)
        ttk.Button(btns, text=_t("ok"), command=self.ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text=_t("cancel"), command=self.cancel).pack(side=tk.LEFT, padx=6)

        self._init_defaults(selected)
        self.var_comp.bind("<<ComboboxSelected>>", lambda _e: self._sync_var_defaults())
        self._sync_measure_visibility()

        self.dialog.wait_window()

    def _init_defaults(self, selected: Optional[Component]):
        def pick_socket_label() -> Optional[str]:
            for s in self._meas_items:
                cid = self._meas_map.get(s)
                c = self.cir.components.get(cid) if cid else None
                if c and c.ctype == "socket":
                    return s
            return None

        if self._var_items:
            initial = self._var_items[0]
            if selected and selected.ctype in ("resistor", "rheostat", "socket"):
                for s in self._var_items:
                    if self._var_map.get(s) == selected.cid:
                        initial = s
                        break
            self.var_comp.set(initial)

        sock_label = pick_socket_label()
        if sock_label:
            self.meas_comp.set(sock_label)
        elif self._meas_items:
            self.meas_comp.set(self._meas_items[0])

        self.meas_field.set("Iab")
        if selected:
            self.node_x.insert(0, str(selected.a[0]))
            self.node_y.insert(0, str(selected.a[1]))
        else:
            self.node_x.insert(0, "0")
            self.node_y.insert(0, "0")
        self._sync_var_defaults()

    def _sync_var_defaults(self):
        cid = self._var_map.get(self.var_comp.get())
        c = self.cir.components.get(cid) if cid else None
        if c and c.ctype == "socket":
            self.var_prop.set("V")
            self.lo.delete(0, tk.END)
            self.hi.delete(0, tk.END)
            self.lo.insert(0, "0")
            self.hi.insert(0, "30")
            return

        self.var_prop.set("R")
        if c and c.ctype == "rheostat":
            lo0 = str(float(c.props.get("Rmin", 0.0)))
            hi0 = str(float(c.props.get("Rmax", max(float(c.props.get("R", 100.0)), 100.0))))
        else:
            lo0, hi0 = "1", "1000"
        self.lo.delete(0, tk.END)
        self.hi.delete(0, tk.END)
        self.lo.insert(0, lo0)
        self.hi.insert(0, hi0)

    def _sync_measure_visibility(self):
        show_comp = (self.measure_kind.get() == "comp")
        state_comp = "normal" if show_comp else "disabled"
        state_node = "normal" if not show_comp else "disabled"
        for w in (self.meas_comp, self.meas_field, self.meas_branch):
            w.configure(state=state_comp)
        if show_comp:
            self.meas_branch.configure(state="normal")
        for w in (self.node_x, self.node_y):
            w.configure(state=state_node)

    def ok(self):
        title = "Goal Seek"
        if callable(self.tr):
            title = self.tr("gs_dialog_title")
        var_cid = self._var_map.get(self.var_comp.get())
        if not var_cid:
            messagebox.showerror(title, self.tr("gs_err_choose_var") if callable(self.tr) else "Please choose a variable component")
            return
        var_prop = (self.var_prop.get() or "").strip() or "R"
        try:
            target = float(self.target.get())
            lo = float(self.lo.get())
            hi = float(self.hi.get())
        except ValueError:
            messagebox.showerror(title, self.tr("gs_err_target_lo_hi") if callable(self.tr) else "Target/Lo/Hi must be numbers")
            return

        if self.measure_kind.get() == "node":
            try:
                nx = int(float(self.node_x.get()))
                ny = int(float(self.node_y.get()))
            except ValueError:
                messagebox.showerror(title, self.tr("gs_err_node_int") if callable(self.tr) else "Node x/y must be integers")
                return
            measure: Dict[str, Any] = {"kind": "node", "node": [nx, ny], "abs": bool(self.node_abs.get())}
        else:
            meas_cid = self._meas_map.get(self.meas_comp.get())
            if not meas_cid:
                messagebox.showerror(title, self.tr("gs_err_choose_meas") if callable(self.tr) else "Please choose a measurement component")
                return
            field = (self.meas_field.get() or "").strip() or "Iab"
            measure = {"kind": "comp", "cid": meas_cid, "field": field, "abs": bool(self.meas_abs.get())}
            br = (self.meas_branch.get() or "").strip()
            if br:
                measure["branch"] = br

        self.result = {
            "var_cid": var_cid,
            "var_prop": var_prop,
            "target": target,
            "lo": lo,
            "hi": hi,
            "measure": measure,
            "reject_overcurrent": bool(self.reject_overcurrent.get()),
            "auto_range": bool(self.auto_range.get()),
        }
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

def main_gui():
    root = tk.Tk()
    app = CircuitGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui()
