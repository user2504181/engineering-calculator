import flet as ft
import math
import cmath
import re
import traceback # Added to catch the exact error line

def main(page: ft.Page):
    try: # --- START DIAGNOSTIC WRAPPER ---
        page.title = "Engineering Calculator"
        # Removed the page.window_width and height that crash Android
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0

        # --- 1. THE NAVIGATION DRAWER (CONSTANTS) ---
        def insert_constant(e):
            current = result_text.value
            val = e.control.data
            if current == "0" or current == "Error":
                result_text.value = val
            else:
                result_text.value += val
            page.close_drawer()
            page.update()

        page.drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(height=12),
                ft.Text("   Constants & Biomedical", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(thickness=2),
                ft.ListTile(title=ft.Text("Faraday Constant (F)"), subtitle=ft.Text("96485.33 C/mol"), data="96485.33", on_click=insert_constant),
                ft.ListTile(title=ft.Text("Permittivity of Free Space (ε₀)"), subtitle=ft.Text("8.854e-12 F/m"), data="8.854e-12", on_click=insert_constant),
                ft.ListTile(title=ft.Text("Planck Constant (h)"), subtitle=ft.Text("6.626e-34 J⋅s"), data="6.626e-34", on_click=insert_constant),
                ft.ListTile(title=ft.Text("Standard Gravity (g)"), subtitle=ft.Text("9.80665 m/s²"), data="9.80665", on_click=insert_constant),
                ft.ListTile(title=ft.Text("Blood Density (approx)"), subtitle=ft.Text("1060 kg/m³"), data="1060", on_click=insert_constant),
                ft.ListTile(title=ft.Text("Resting Membrane Potential"), subtitle=ft.Text("-70 mV"), data="-70e-3", on_click=insert_constant),
            ]
        )

        # --- 2. SCIENTIFIC TAB LOGIC ---
        memory = 0
        history = []
        angle_mode = "DEG"
        shift_active = False
        shift_button_ref = None

        result_text = ft.Text(value="0", size=48, text_align=ft.TextAlign.RIGHT, weight=ft.FontWeight.BOLD)
        history_text = ft.Text(value="", size=16, color=ft.colors.GREY_400, text_align=ft.TextAlign.RIGHT)

        def safe_sin(x): return cmath.sin(math.radians(x.real) if angle_mode == "DEG" else x)
        def safe_cos(x): return cmath.cos(math.radians(x.real) if angle_mode == "DEG" else x)
        def safe_sqrt(x): return cmath.sqrt(x) 

        safe_env = {
            "sin": safe_sin, "cos": safe_cos, "tan": cmath.tan,
            "log": cmath.log10, "ln": cmath.log, "sqrt": safe_sqrt,
            "pi": math.pi, "e": math.e, "j": 1j, "factorial": math.factorial
        }

        def format_complex(c):
            if isinstance(c, complex):
                if abs(c.imag) < 1e-10: return str(round(c.real, 8))
                if abs(c.real) < 1e-10: return str(round(c.imag, 8)) + "j"
                return f"{round(c.real, 8)}{'+' if c.imag > 0 else ''}{round(c.imag, 8)}j"
            return str(round(c, 8)) if isinstance(c, float) else str(c)

        def button_clicked(e):
            nonlocal memory, shift_active, angle_mode
            data = e.control.data
            current = result_text.value

            if current == "Error": current = "0"

            if data == "MENU":
                page.open_drawer() # Adjusted for modern Flet
            elif data == "SHIFT":
                shift_active = not shift_active
                shift_button_ref.bgcolor = ft.colors.AMBER_700 if shift_active else ft.colors.BLUE_GREY_700
                page.update()
                return
            elif data == "AC":
                result_text.value, history_text.value, shift_active = "0", "", False
                if shift_button_ref: shift_button_ref.bgcolor = ft.colors.BLUE_GREY_700
            elif data == "C":
                result_text.value = current[:-1] if len(current) > 1 else "0"
            elif data == "=":
                try:
                    expr = current.replace("×", "*").replace("÷", "/").replace("^", "**").replace("²", "**2").replace("√", "sqrt")
                    expr = expr.replace("π", "pi")
                    expr = re.sub(r'(\d+\.?\d*)!', r'factorial(\1)', expr)
                    expr = re.sub(r'(\d)\(', r'\1*(', expr) 
                    expr = re.sub(r'\)(\d)', r')*\1', expr)  
                    expr = re.sub(r'\)\(', r')*(', expr)     
                    
                    result = eval(expr, {"__builtins__": {}}, safe_env)
                    history_text.value = current + " ="
                    result_text.value = format_complex(result)
                except Exception:
                    result_text.value = "Error"
            else:
                append_val = data
                if data in ["sin", "cos", "tan", "log", "ln"]: append_val += "("
                elif data == "√": append_val = "sqrt("
                elif data == "x²": append_val = "²"
                elif data == "xʸ": append_val = "^"
                
                if current == "0" and append_val not in ["+", "-", "×", "÷", "^", "²", "."]:
                    result_text.value = append_val
                else:
                    result_text.value = current + append_val
            page.update()

        def create_btn(text, color=ft.colors.BLUE_GREY_800, text_color=ft.colors.WHITE, expand=1, small=False):
            btn = ft.Container(
                content=ft.Text(text, size=18 if small else 22, color=text_color, weight=ft.FontWeight.W_500),
                alignment=ft.alignment.center, bgcolor=color, border_radius=12,
                on_click=button_clicked, data=text, expand=expand, height=50 if small else 60
            )
            if text == "SHIFT":
                nonlocal shift_button_ref
                shift_button_ref = btn
            return btn

        display_area = ft.Container(
            content=ft.Column([history_text, result_text], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END),
            padding=20, bgcolor=ft.colors.BLACK, height=150, alignment=ft.alignment.bottom_right
        )

        keyboard = ft.Column([
            ft.Row([create_btn("MENU", ft.colors.INDIGO_600, small=True), create_btn("SHIFT", ft.colors.BLUE_GREY_700, small=True), create_btn("sin", ft.colors.BLUE_GREY_700, small=True), create_btn("cos", ft.colors.BLUE_GREY_700, small=True), create_btn("tan", ft.colors.BLUE_GREY_700, small=True)], spacing=8),
            ft.Row([create_btn("j", ft.colors.PURPLE_500, small=True), create_btn("π", ft.colors.BLUE_GREY_700, small=True), create_btn("log", ft.colors.BLUE_GREY_700, small=True), create_btn("√", ft.colors.BLUE_GREY_700, small=True), create_btn("x²", ft.colors.BLUE_GREY_700, small=True)], spacing=8),
            ft.Row([create_btn("AC", ft.colors.RED_400), create_btn("C", ft.colors.ORANGE_400), create_btn("(", ft.colors.BLUE_GREY_600), create_btn(")", ft.colors.BLUE_GREY_600), create_btn("÷", ft.colors.ORANGE_500)], spacing=8),
            ft.Row([create_btn("7"), create_btn("8"), create_btn("9"), create_btn("×", ft.colors.ORANGE_500)], spacing=8),
            ft.Row([create_btn("4"), create_btn("5"), create_btn("6"), create_btn("-", ft.colors.ORANGE_500)], spacing=8),
            ft.Row([create_btn("1"), create_btn("2"), create_btn("3"), create_btn("+", ft.colors.ORANGE_500)], spacing=8),
            ft.Row([create_btn("0", expand=2), create_btn("."), create_btn("=", ft.colors.ORANGE_600)], spacing=8)
        ], spacing=8, expand=True)

        scientific_tab = ft.Container(content=ft.Column([display_area, keyboard]), padding=10)

        # --- 3. MATRIX / STATE-SPACE TAB ---
        m11 = ft.TextField(label="A11", width=80, value="1")
        m12 = ft.TextField(label="A12", width=80, value="0")
        m21 = ft.TextField(label="A21", width=80, value="0")
        m22 = ft.TextField(label="A22", width=80, value="1")
        matrix_output = ft.Text(value="Determinant: 1\nEigenvalues: 1, 1", size=20)

        def calculate_matrix(e):
            try:
                a, b, c, d = float(m11.value), float(m12.value), float(m21.value), float(m22.value)
                det = (a * d) - (b * c)
                trace = a + d
                discriminant = cmath.sqrt(trace**2 - 4*det)
                eig1 = (trace + discriminant) / 2
                eig2 = (trace - discriminant) / 2
                matrix_output.value = f"Determinant: {round(det, 4)}\nEigenvalues:\nλ1 = {format_complex(eig1)}\nλ2 = {format_complex(eig2)}"
            except Exception:
                matrix_output.value = "Invalid Matrix Input"
            page.update()

        matrix_tab = ft.Container(
            content=ft.Column([
                ft.Text("2x2 State-Space A-Matrix Analyzer", weight=ft.FontWeight.BOLD, size=18),
                ft.Row([m11, m12], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([m21, m22], alignment=ft.MainAxisAlignment.CENTER),
                ft.ElevatedButton("Calculate", on_click=calculate_matrix, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
                ft.Divider(),
                matrix_output
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20
        )

        # --- 4. LIVE GRAPHING TAB ---
        graph_input = ft.TextField(label="f(x) =", value="sin(x)", expand=True)
        chart = ft.LineChart(
            data_series=[], border=ft.border.all(1, ft.colors.GREY_400),
            min_x=-10, max_x=10, min_y=-5, max_y=5, expand=True
        )

        def plot_graph(e):
            try:
                func_str = graph_input.value.replace("sin", "math.sin").replace("cos", "math.cos").replace("^", "**")
                points = []
                for i in range(-100, 101, 4):
                    x = i / 10.0
                    try:
                        y = eval(func_str, {"math": math, "x": x})
                        if isinstance(y, (int, float)) and -100 < y < 100:
                            points.append(ft.LineChartDataPoint(x, y))
                    except Exception:
                        continue
                chart.data_series = [ft.LineChartData(data_points=points, stroke_width=3, color=ft.colors.CYAN_400)]
                chart.update()
            except Exception:
                pass

        graph_tab = ft.Container(
            content=ft.Column([
                ft.Row([graph_input, ft.ElevatedButton("Plot", on_click=plot_graph, bgcolor=ft.colors.ORANGE_600, color=ft.colors.WHITE)]),
                chart
            ]),
            padding=10
        )

        # --- ASSEMBLE TABS ---
        t = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Scientific", content=scientific_tab),
                ft.Tab(text="Matrix (A)", content=matrix_tab),
                ft.Tab(text="Graph", content=graph_tab),
            ],
            expand=1
        )

        page.add(t)
        page.update()

    # --- CATCH FATAL CRASHES AND DISPLAY THEM ---
    except Exception as e:
        page.clean()
        page.add(
            ft.Text("SYSTEM BOOT CRASH", size=24, color=ft.colors.RED_500, weight=ft.FontWeight.BOLD),
            ft.Text(f"Error: {str(e)}", color=ft.colors.RED_300, size=16),
            ft.Text("Traceback Log:", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
            ft.Text(traceback.format_exc(), size=12, color=ft.colors.GREY_400, selectable=True)
        )
        page.update()

ft.app(target=main)
                
    
