"""C language practice problems imported from the exercise handout.

The handout contains interactive exercises (20 and 21) as well as deterministic
standard-I/O exercises.  The latter use deliberately small but varied test
sets so they can be used by the existing judge worker.
"""

from math import sqrt


def _tc(input_data, output_data):
    return {"input": str(input_data), "output": str(output_data)}


def _generated_cases(values, input_fn, output_fn):
    cases = []
    for value in values:
        args = value if isinstance(value, tuple) else (value,)
        cases.append(_tc(input_fn(*args), output_fn(*args)))
    return cases


def _problem(source_number, title, description, input_format, output_format,
             samples, test_cases, tags, difficulty="简单", interactive=False):
    return {
        "id": 2000 + source_number,
        "sourceNumber": source_number,
        "category": "c-language",
        "categoryLabel": "C 语言专区",
        "title": title,
        "difficulty": difficulty,
        "tags": tags,
        "description": description,
        "inputFormat": input_format,
        "outputFormat": output_format,
        "samples": samples,
        "testCases": test_cases,
        "interactive": interactive,
        "judgeable": not interactive,
        "timeLimit": 1000,
        "memoryLimit": 256,
    }


def _max2(a, b):
    return f"max={max(a, b)}"


def _max3(a, b, c):
    return f"max={max(a, b, c)}"


def _avg2(a, b):
    value = (a + b) / 2
    return f"平均值为{value:g}"


def _celsius(fahrenheit):
    return f"摄氏度={5 * (fahrenheit - 32) / 9:.6f}"


def _is_leap(year):
    return f"{year}是{'闰年' if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0) else '非闰年'}"


def _triangle(a, b, c):
    if a + b <= c or a + c <= b or b + c <= a:
        return "无法构成三角形"
    half = (a + b + c) / 2
    return f"三角形面积:{sqrt(half * (half - a) * (half - b) * (half - c)):.6f}"


def _piecewise(x):
    value = x if x < 1 else 2 * x - 1 if x < 10 else 3 * x + 11
    return f"y={value:.6f}"


def _ticket(age):
    price = 0 if age >= 70 else 10 if age < 7 else 20 if age >= 50 else 50
    return f"ticket={price}"


def _electricity(units):
    if units <= 100:
        fee = units * 0.5
    elif units <= 200:
        fee = 100 * 0.5 + (units - 100) * 0.6
    else:
        fee = 100 * 0.5 + 100 * 0.6 + (units - 200) * 0.8
    return f"电费={fee:.2f}"


def _quadratic(a, b, c):
    delta = b * b - 4 * a * c
    if delta < 0 or a == 0:
        return "无解"
    root = sqrt(delta)
    return f"解1={(-b + root) / (2 * a):.6f},解2={(-b - root) / (2 * a):.6f}"


def _growth(rate, years):
    return f"{years}年后增长百分比为: {(1 + rate) ** years:.6f}"


def _grade_band(letter):
    return {"A": "成绩>=90", "B": "成绩>=80", "C": "成绩>=70", "D": "成绩>=60", "E": "成绩<60"}[letter]


def _grade(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"


def _tower(x, y):
    towers = ((2, 2, 20), (-2, 2, 26), (-2, -2, 30), (2, -2, 40))
    for cx, cy, height in towers:
        if (x - cx) ** 2 + (y - cy) ** 2 <= 1:
            return f"高度={height:.6f}米"
    return "不在塔区域内"


def _calculator(a, op, b):
    if op == "+":
        value = a + b
    elif op == "-":
        value = a - b
    elif op == "*":
        value = a * b
    else:
        value = a / b
    return f"result={value:.6f}"


def _donation(*amounts):
    total = 0.0
    count = 0
    for amount in amounts:
        total += amount
        count += 1
        if total >= 10000 or count > 5:
            break
    return f"金额={total:.6f},人数={count}"


def _sqrt_iter(value):
    return f"{sqrt(value):.4f}"


def _matrix_case(rows, shared, left, right):
    right_cols = len(right) // shared
    left_rows = [left[i * shared:(i + 1) * shared] for i in range(rows)]
    right_rows = [right[i * right_cols:(i + 1) * right_cols] for i in range(shared)]
    result = []
    for row in left_rows:
        result.append(" ".join(str(sum(row[k] * right_rows[k][j] for k in range(shared))) for j in range(right_cols)))
    return "\n".join(result)


def _matrix_input(rows, shared, left, right):
    right_cols = len(right) // shared
    return f"{rows} {shared} {shared} {right_cols} " + " ".join(map(str, left + right))


def _avg_scores(*scores):
    return f"平均成绩为{sum(scores) / len(scores):.6f}"


def _join_numbers(*numbers):
    return " ".join(str(number) for number in numbers)


def _variance(*numbers):
    average = sum(numbers) / len(numbers)
    return f"方差为{sum((number - average) ** 2 for number in numbers) / len(numbers):.6f}"


def _range_value(*numbers):
    return f"极差为{max(numbers) - min(numbers):.6f}"


def _insert_case(numbers, value):
    result = sorted((*numbers, value))
    return " ".join(map(str, result))


def _letter_frequency(text, letter):
    letters = [char.lower() for char in text if char.isalpha() and char.isascii()]
    count = letters.count(letter.lower())
    frequency = count / len(letters) if letters else 0
    return f"字母总数={len(letters)},次数={count},频率={frequency:.6f}"


def _pow_value(x, n):
    return f"{x}^{n}={x ** n:g}"


def _lcm(a, b):
    left, right = abs(a), abs(b)
    while right:
        left, right = right, left % right
    gcd = left or 1
    return f"最小公倍数{abs(a * b) // gcd}"


def _factorial(n):
    value = 1
    for i in range(2, n + 1):
        value *= i
    return f"n的阶乘为{value}"


def _dynamic_average(*numbers):
    return f"平均值为{sum(numbers) / len(numbers):.6f}"


def _descending(*numbers):
    return " ".join(f"{number:.3f}" for number in sorted(numbers, reverse=True))


def _max_matrix(rows, values):
    return f"最大值为{max(values)}"


def _linked_list(new_num, new_score):
    return "\n".join([
        "1 89.500000",
        "2 90.000000",
        f"{new_num} {new_score:.6f}",
        "4 85.000000",
    ])


def _segments(*scores):
    counts = [0] * 10
    for score in scores:
        counts[min(max(int(score) // 10, 0), 9)] += 1
    lines = []
    for index in range(9, -1, -1):
        upper = 100 if index == 9 else index * 10 + 9
        lines.append(f"{index * 10}-{upper}: {counts[index]}人")
    return "\n".join(lines)


def _votes(*names):
    counts = {"zhang": 0, "li": 0, "sun": 0}
    for name in names:
        if name in counts:
            counts[name] += 1
    return "\n".join(f"{name}:{counts[name]}" for name in ("zhang", "li", "sun"))


def _array_average(*numbers):
    return f"{sum(numbers) / len(numbers):.2f}"


def _add_problem(source_number, title, description, input_format, output_format,
                 samples, test_cases, tags, difficulty="简单", interactive=False):
    item = _problem(source_number, title, description, input_format, output_format,
                    samples, test_cases, tags, difficulty, interactive)
    C_LANGUAGE_PROBLEMS[item["id"]] = item


C_LANGUAGE_PROBLEMS = {}

_add_problem(1, "两个数求最大值", "输入两个整数，通过自定义函数输出较大值。", "一行两个整数 a、b。", "输出 max=<最大值>。", [{"input": "56 52", "output": "max=56"}], _generated_cases([(56, 52), (-3, -8), (0, 0), (100, 99), (-5, 7)], lambda a, b: f"{a} {b}", _max2), ["函数", "分支"])
_add_problem(2, "三个数求最大值", "输入三个整数，通过函数求最大值。", "一行三个整数。", "输出 max=<最大值>。", [{"input": "5 6 3", "output": "max=6"}], _generated_cases([(5, 6, 3), (-1, -2, -3), (7, 7, 2), (0, 100, 50), (999, 1, 998)], lambda a, b, c: f"{a} {b} {c}", _max3), ["函数", "分支"])
_add_problem(3, "两个数平均值", "输入两个整数并计算算术平均值。", "一行两个整数。", "输出 平均值为<结果>。", [{"input": "6 10", "output": "平均值为8"}], _generated_cases([(6, 10), (1, 2), (-5, 5), (0, 1), (100, 101)], lambda a, b: f"{a} {b}", _avg2), ["运算", "函数"])
_add_problem(4, "温度转换（华氏转摄氏）", "使用 C=5*(F-32)/9 将华氏温度转换为摄氏温度。", "一个实数 F。", "输出 摄氏度=，保留 6 位小数。", [{"input": "41", "output": "摄氏度=5.000000"}], _generated_cases([-40, 0, 32, 41, 98.6], str, _celsius), ["浮点数", "公式"])
_add_problem(5, "闰年判断", "按能被 4 整除但不能被 100 整除，或能被 400 整除的规则判断闰年。", "一个整数年份。", "输出“年份是闰年”或“年份是非闰年”。", [{"input": "1900", "output": "1900是非闰年"}], _generated_cases([1900, 2000, 2024, 2023, 2100], str, _is_leap), ["条件", "取余"])
_add_problem(6, "三角形面积（海伦公式）", "判断三边能否构成三角形，能则用海伦公式求面积。", "一行三个正实数边长。", "可行时输出三角形面积:，保留 6 位小数；否则输出无法构成三角形。", [{"input": "3 4 5", "output": "三角形面积:6.000000"}], _generated_cases([(3, 4, 5), (2, 2, 3), (1, 2, 3), (5, 5, 6), (1.5, 2, 2.5)], lambda a, b, c: f"{a} {b} {c}", _triangle), ["数学", "函数"])
_add_problem(7, "分段函数", "按 x<1、1≤x<10、x≥10 三段计算 y=x、y=2x-1、y=3x+11。", "一个实数 x。", "输出 y=，保留 6 位小数。", [{"input": "0.5", "output": "y=0.500000"}], _generated_cases([0.5, 1, 9.999, 10, -3], str, _piecewise), ["条件", "分段函数"])
_add_problem(8, "阶梯门票", "根据年龄计算门票：70 岁及以上 0 元，7 岁以下 10 元，50-69 岁 20 元，其余 50 元。", "一个整数年龄。", "输出 ticket=<价格>。", [{"input": "50", "output": "ticket=20"}], _generated_cases([0, 6, 7, 30, 50, 69, 70, 100], str, _ticket), ["条件", "分段"])
_add_problem(9, "阶梯电费", "按 0-100、101-200、200 以上的阶梯单价计算电费。", "一个非负实数用电量。", "输出 电费=，保留 2 位小数。", [{"input": "26", "output": "电费=13.00"}], _generated_cases([0, 26, 100, 101, 200, 250], str, _electricity), ["条件", "浮点数"], "中等")
_add_problem(10, "一元二次方程求解", "计算 ax²+bx+c=0 的实根；判别式小于 0 或 a 为 0 时输出无解。", "一行三个实数 a、b、c。", "有实根时输出解1、解2，各保留 6 位小数；否则输出无解。", [{"input": "1 6 9", "output": "解1=-3.000000,解2=-3.000000"}], _generated_cases([(1, 6, 9), (1, -5, 6), (2, 0, -8), (1, 0, 1), (0, 2, 3)], lambda a, b, c: f"{a} {b} {c}", _quadratic), ["math.h", "判别式"], "中等")
_add_problem(11, "pow 函数（国民生产总值增长）", "根据 p=(1+r)^n 计算 n 年后的增长倍数。", "一行实数增长率 r 和整数年数 n。", "输出 n年后增长百分比为:，保留 6 位小数。", [{"input": "0.3 6", "output": "6年后增长百分比为: 4.826809"}], _generated_cases([(0.3, 6), (0, 5), (0.1, 1), (-0.1, 2), (1, 3)], lambda r, n: f"{r} {n}", _growth), ["math.h", "幂运算"])
_add_problem(12, "switch-case 五级制成绩", "将 A-E 五级制成绩转换为对应分数段。", "一个字符 A-E。", "输出该等级的成绩范围说明。", [{"input": "A", "output": "成绩>=90"}], _generated_cases(["A", "B", "C", "D", "E"], str, _grade_band), ["switch", "字符"])
_add_problem(13, "case 成绩转换", "将 0-100 的百分制成绩转换为 A-E 等级。", "一个 0-100 的整数成绩。", "输出 A、B、C、D 或 E。", [{"input": "95", "output": "A"}], _generated_cases([0, 59, 60, 69, 70, 79, 80, 89, 90, 100], str, _grade)[:5], ["switch", "成绩"])
_add_problem(14, "高塔高度判断（坐标）", "判断点是否落在四个半径为 1 的圆形塔区域内，并输出对应塔高。", "一行两个实数 x、y。", "命中时输出高度=xx.xxxxxx米，否则输出不在塔区域内。", [{"input": "2 2", "output": "高度=20.000000米"}], _generated_cases([(2, 2), (-2, 2), (-2, -2), (2, -2), (0, 0)], lambda x, y: f"{x} {y}", _tower), ["坐标", "math.h"], "中等")
_add_problem(15, "简易计算器", "使用加、减、乘、除完成两个实数的计算。", "一行：实数 a、运算符 op（+ - * /）、实数 b。", "输出 result=，保留 6 位小数。", [{"input": "1 + 3", "output": "result=4.000000"}], _generated_cases([(1, "+", 3), (8, "-", 3), (2.5, "*", 4), (7, "/", 2), (-2, "+", 5)], lambda a, op, b: f"{a} {op} {b}", _calculator), ["switch", "运算"])
_add_problem(18, "捐款累计", "逐个读入捐款，累计金额达到 10000 元或人数超过 5 人时停止。", "输入若干个捐款金额，直到程序停止或输入结束。", "输出 金额=，人数=。", [{"input": "3000 3000 3000 3000", "output": "金额=12000.000000,人数=4"}], _generated_cases([(3000, 3000, 3000, 3000), (5000, 4000, 1000), (100, 100, 100, 100, 100, 100), (12000,), (2500, 2500, 2500, 2500)], lambda *amounts: " ".join(map(str, amounts)), _donation), ["循环", "累计"])
_add_problem(19, "迭代法求平方根", "用牛顿迭代法求正数平方根，直到误差小于 1e-5。", "一个正实数 a。", "输出平方根，保留 4 位小数。", [{"input": "2", "output": "1.4142"}], _generated_cases([0.25, 1, 2, 10, 100], str, _sqrt_iter), ["循环", "迭代"], "中等")
_add_problem(20, "猜数字游戏", "随机生成目标数，在限定次数内反复猜测并提示大小。", "输入游戏次数和随机数上限，再输入猜测值。", "这是随机交互练习，不参与自动判题。", [], [], ["随机数", "交互"], "简单", True)
_add_problem(21, "算术闯关游戏", "随机生成加法题，答对进入下一关，答错结束并按关卡计分。", "输入闯关次数和数字上限，再输入每关答案。", "这是随机交互练习，不参与自动判题。", [], [], ["随机数", "循环"], "简单", True)
_add_problem(22, "矩阵乘法", "计算两个可相乘矩阵的乘积。", "输入 r1 c1 r2 c2，随后输入两个矩阵元素。", "按行输出乘积矩阵，元素以单个空格分隔。", [{"input": "2 3 3 2 1 2 3 4 5 6 1 2 3 4 5 6", "output": "22 28\n49 64"}], [
    _tc(_matrix_input(2, 3, [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]), _matrix_case(2, 3, [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])),
    _tc(_matrix_input(1, 2, [2, 3], [4, 5]), _matrix_case(1, 2, [2, 3], [4, 5])),
    _tc(_matrix_input(3, 1, [1, 2, 3], [4, 5, 6]), _matrix_case(3, 1, [1, 2, 3], [4, 5, 6])),
    _tc(_matrix_input(2, 2, [1, 0, 0, 1], [7, 8, 9, 10]), _matrix_case(2, 2, [1, 0, 0, 1], [7, 8, 9, 10])),
    _tc(_matrix_input(2, 2, [-1, 2, 3, -4], [2, 0, 1, 5]), _matrix_case(2, 2, [-1, 2, 3, -4], [2, 0, 1, 5])),
], ["二维数组", "矩阵"], "中等")
_add_problem(23, "平均成绩计算", "循环输入 10 个成绩并求平均值。", "一行或多行共 10 个成绩。", "输出平均成绩为，保留 6 位小数。", [{"input": "80 85 90 75 95 70 65 88 92 78", "output": "平均成绩为81.800000"}], _generated_cases([(80, 85, 90, 75, 95, 70, 65, 88, 92, 78), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (100, 100, 100, 100, 100, 100, 100, 100, 100, 100), (60, 70, 80, 90, 60, 70, 80, 90, 60, 70), (59, 59, 59, 59, 59, 59, 59, 59, 59)], lambda *scores: " ".join(map(str, scores)), _avg_scores), ["循环", "平均值"])
_add_problem(24, "数组平均值", "输入 5 个整数，计算平均值并保留两位小数。", "一行 5 个整数。", "输出不带标签的平均值，保留 2 位小数。", [{"input": "1 2 3 4 5", "output": "3.00"}], _generated_cases([(1, 2, 3, 4, 5), (0, 0, 0, 0, 1), (-5, -4, -3, -2, -1), (10, 20, 30, 40, 50), (1, 1, 2, 2, 3)], lambda *numbers: " ".join(map(str, numbers)), _array_average), ["数组", "平均值"])
_add_problem(25, "冒泡排序", "使用冒泡排序将数组升序排列。", "输入 n 和 n 个整数。", "输出排序后的 n 个整数，单个空格分隔。", [{"input": "5 9 7 5 6 2", "output": "2 5 6 7 9"}], _generated_cases([(5, 9, 7, 5, 6, 2), (1, 8), (5, 1, 2, 3, 4, 5), (6, 3, -1, 3, 0, 2, -5), (4, 0, 0, 0, 0)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _join_numbers(*sorted(numbers))), ["数组", "排序"])
_add_problem(26, "数组方差", "先求平均值，再按 Σ(xi-平均值)²/N 计算方差。", "输入 n 和 n 个实数。", "输出方差为，保留 6 位小数。", [{"input": "5 1 2 3 4 5", "output": "方差为2.000000"}], _generated_cases([(5, 1, 2, 3, 4, 5), (1, 7), (4, 0, 0, 0, 0), (3, -1, 0, 1), (6, 1, 1, 2, 2, 3, 3)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _variance(*numbers)), ["数组", "数学"], "中等")
_add_problem(27, "数组极差", "求数组最大值与最小值之差。", "输入 n 和 n 个实数。", "输出极差为，保留 6 位小数。", [{"input": "5 1 5 3 9 2", "output": "极差为8.000000"}], _generated_cases([(5, 1, 5, 3, 9, 2), (1, 7), (4, -5, -1, -9, -3), (3, 0, 0, 0), (6, 1.5, 2.5, -1, 8, 4, 3)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _range_value(*numbers)), ["数组", "打擂台"])
_add_problem(28, "成绩矩阵统计", "计算成绩矩阵每行和每列平均值。", "输入 r c 和 r*c 个成绩。", "先输出每行平均值，再输出每列平均值，均保留 2 位小数。", [{"input": "2 3 90 80 70 60 75 85", "output": "80.00 73.33\n75.00 77.50 77.50"}], [
    _tc("2 3 90 80 70 60 75 85", "80.00 73.33\n75.00 77.50 77.50"),
    _tc("1 1 100", "100.00\n100.00"),
    _tc("3 2 1 2 3 4 5 6", "1.50 3.50 5.50\n3.00 4.00"),
    _tc("2 2 0 100 50 50", "50.00 50.00\n25.00 75.00"),
    _tc("2 4 -1 -2 -3 -4 4 3 2 1", "-2.50 2.50\n1.50 0.50 -0.50 -1.50"),
], ["二维数组", "统计"], "中等")
_add_problem(29, "有序数组插入", "将新元素插入升序数组并保持有序。", "输入 n、n 个升序整数和待插入值 x。", "输出插入后的 n+1 个整数。", [{"input": "5 1 3 5 7 9 4", "output": "1 3 4 5 7 9"}], _generated_cases([((1, 3, 5, 7, 9), 4), ((2, 4, 6), 0), ((2, 4, 6), 8), ((1, 1, 2), 1), ((-3, -1, 2), -2)], lambda numbers, value: f"{len(numbers)} " + " ".join(map(str, numbers)) + f" {value}", _insert_case), ["数组", "插入"])
_add_problem(30, "字母频率统计", "统计字符串中的英文字母总数，以及指定字母的出现次数和频率。", "一行字符串，下一项为待统计字母。", "输出字母总数、次数和频率，频率保留 6 位小数。", [{"input": "HelloWorld l", "output": "字母总数=10,次数=3,频率=0.300000"}], _generated_cases([("HelloWorld", "l"), ("ABCabc", "a"), ("123 !", "a"), ("Mississippi", "s"), ("ZzZ", "z")], lambda text, letter: f"{text}\n{letter}", _letter_frequency), ["字符串", "字符统计"])
_add_problem(31, "自定义 pow 函数", "用递推方式实现整数幂运算。", "输入整数底数 x 和非负整数指数 n。", "输出 x^n=<结果>。", [{"input": "2 10", "output": "2^10=1024"}], _generated_cases([(2, 10), (5, 0), (-2, 3), (10, 2), (3, 5)], lambda x, n: f"{x} {n}", _pow_value), ["函数", "递推"])
_add_problem(32, "闰年判断函数", "通过自定义函数判断年份是否为闰年。", "一个整数年份。", "输出“年份是闰年”或“年份是非闰年”。", [{"input": "1900", "output": "1900是非闰年"}], _generated_cases([1900, 2000, 2024, 2023, 2400], str, _is_leap), ["函数", "条件"])
_add_problem(33, "三角形面积函数", "通过自定义函数使用海伦公式求三角形面积。", "一行三个正实数边长。", "输出三角形面积:，保留 6 位小数；不能构成三角形时输出无法构成三角形。", [{"input": "3 4 5", "output": "三角形面积:6.000000"}], _generated_cases([(3, 4, 5), (2, 2, 3), (1, 2, 3), (5, 5, 6), (2.5, 3, 4)], lambda a, b, c: f"{a} {b} {c}", _triangle), ["函数", "数学"])
_add_problem(34, "字母判断函数", "通过自定义函数判断字符是否为英文字母。", "一个 ASCII 字符。", "输出“字符是英文字母”或“字符不是英文字母”。", [{"input": "A", "output": "A是英文字母"}], _generated_cases(["A", "z", "0", "#", "m"], str, lambda char: f"{char}{'是' if char.isalpha() else '不是'}英文字母"), ["函数", "字符"])
_add_problem(35, "最小公倍数函数", "通过自定义函数求两个正整数的最小公倍数。", "一行两个正整数。", "输出最小公倍数<结果>。", [{"input": "12 18", "output": "最小公倍数36"}], _generated_cases([(12, 18), (1, 7), (6, 8), (21, 14), (100, 25)], lambda a, b: f"{a} {b}", _lcm), ["函数", "最大公约数"])
_add_problem(36, "数组平均值函数", "通过自定义函数求数组平均值。", "输入 n 和 n 个实数。", "输出平均值为，保留 6 位小数。", [{"input": "5 1 2 3 4 5", "output": "平均值为3.000000"}], _generated_cases([(5, 1, 2, 3, 4, 5), (1, 9), (4, -2, 0, 2, 4), (3, 1.5, 2.5, 3.5), (6, 10, 20, 30, 40, 50, 60)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _dynamic_average(*numbers)), ["函数", "数组"])
_add_problem(37, "递归求阶乘", "使用递归函数计算 n 的阶乘，规定 0!=1。", "一个 0-12 的整数 n。", "输出 n的阶乘为<结果>。", [{"input": "5", "output": "n的阶乘为120"}], _generated_cases([0, 1, 5, 10, 12], str, _factorial), ["递归", "函数"])
_add_problem(38, "递归求学生年龄", "第 1 个学生 10 岁，之后每个学生比前一个大 2 岁。", "一个正整数 n。", "输出第 n 个学生的年龄。", [{"input": "1", "output": "10"}], _generated_cases([1, 2, 5, 10, 20], str, lambda n: str(10 + 2 * (n - 1))), ["递归", "函数"])
_add_problem(39, "指针输入输出整数", "通过指针访问数组，输入并输出 5 个整数。", "一行 5 个整数。", "输出 5 个整数，单个空格分隔。", [{"input": "10 20 30 40 50", "output": "10 20 30 40 50"}], _generated_cases([(10, 20, 30, 40, 50), (1, 2, 3, 4, 5), (0, 0, 0, 0, 0), (-1, -2, -3, -4, -5), (9, 7, 5, 3, 1)], lambda *numbers: " ".join(map(str, numbers)), _join_numbers), ["指针", "数组"])
_add_problem(40, "函数指针求最大值", "通过函数指针调用 max 函数求两个整数的最大值。", "一行两个整数。", "输出 max=<最大值>。", [{"input": "56 52", "output": "max=56"}], _generated_cases([(56, 52), (1, 9), (-3, -2), (0, 0), (100, -100)], lambda a, b: f"{a} {b}", _max2), ["指针", "函数"])
_add_problem(41, "指针动态数组求平均值", "使用 calloc 动态分配数组，通过指针输入并求平均值。", "输入 n 和 n 个实数。", "输出平均值为，保留 6 位小数。", [{"input": "5 1 2 3 4 5", "output": "平均值为3.000000"}], _generated_cases([(5, 1, 2, 3, 4, 5), (1, 2.5), (3, -1, 0, 1), (4, 10, 20, 30, 40), (6, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _dynamic_average(*numbers)), ["指针", "动态内存"], "中等")
_add_problem(42, "指针动态数组排序", "使用 calloc 和指针将数组按降序排列。", "输入 n 和 n 个实数。", "输出降序结果，保留 3 位小数，单个空格分隔。", [{"input": "5 3 1 4 1 5", "output": "5.000 4.000 3.000 1.000 1.000"}], _generated_cases([(5, 3, 1, 4, 1, 5), (1, 2), (4, -1, 0, 5, 2), (3, 1.5, 1.25, 3.75), (5, 0, 0, -2, 2, 1)], lambda n, *numbers: f"{n} " + " ".join(map(str, numbers)), lambda n, *numbers: _descending(*numbers)), ["指针", "排序"], "中等")
_add_problem(43, "二维数组求最大值", "通过函数遍历列数固定为 4 的二维数组并求最大值。", "输入行数 m，随后输入 m*4 个整数。", "输出最大值为<结果>。", [{"input": "2 1 2 3 4 5 6 7 8", "output": "最大值为8"}], [
    _tc("2 1 2 3 4 5 6 7 8", "最大值为8"),
    _tc("1 -1 -2 -3 -4", "最大值为-1"),
    _tc("3 0 10 -2 4 8 6 7 1 9 2 3 5", "最大值为10"),
    _tc("2 100 99 98 97 -1 -2 -3 -4", "最大值为100"),
    _tc("4 1 1 1 1 2 2 2 2 3 3 3 3 4 4 4 4", "最大值为4"),
], ["二维数组", "函数"])
_add_problem(44, "链表动态插入节点", "建立包含 1、2、4 号学生的链表，将新节点插入 2 号和 4 号之间。", "输入新节点学号和成绩。", "按链表顺序输出四行“学号 成绩”，成绩保留 6 位小数。", [{"input": "3 95", "output": "1 89.500000\n2 90.000000\n3 95.000000\n4 85.000000"}], _generated_cases([(3, 95), (5, 78), (10, 0), (99, 100), (-1, 66.5)], lambda number, score: f"{number} {score}", _linked_list), ["结构体", "链表"], "中等")
_add_problem(45, "链表插入", "用 show 函数遍历链表，并将新节点插入 2 号和 4 号节点之间。", "输入新节点学号和成绩。", "按链表顺序输出四行“学号 成绩”，成绩保留 6 位小数。", [{"input": "3 95", "output": "1 89.500000\n2 90.000000\n3 95.000000\n4 85.000000"}], _generated_cases([(3, 95), (5, 78), (7, 88.25), (0, 60), (100, 100)], lambda number, score: f"{number} {score}", _linked_list), ["结构体", "链表", "函数"], "中等")
_add_problem(46, "成绩分段统计", "统计成绩落在 0-9、10-19、…、90-100 各段的人数。", "输入学生人数 n 和 n 个成绩。", "从 90-100 段到 0-9 段逐行输出“下限-上限: x人”。", [{"input": "5 95 85 75 65 55", "output": "90-100: 1人\n80-89: 1人\n70-79: 1人\n60-69: 1人\n50-59: 1人\n40-49: 0人\n30-39: 0人\n20-29: 0人\n10-19: 0人\n0-9: 0人"}], [
    _tc("5 95 85 75 65 55", _segments(95, 85, 75, 65, 55)),
    _tc("3 100 50 0", _segments(100, 50, 0)),
    _tc("4 9 10 89 90", _segments(9, 10, 89, 90)),
    _tc("1 77", _segments(77)),
    _tc("6 0 20 40 60 80 100", _segments(0, 20, 40, 60, 80, 100)),
], ["动态内存", "统计"], "中等")
_add_problem(47, "候选人投票统计", "统计 zhang、li、sun 三位候选人的投票数，未知姓名不计票。", "输入投票人数 n 和 n 个姓名。", "依次输出 zhang、li、sun 的票数，每行一个。", [{"input": "10 zhang li sun zhang li zhang sun li zhang li", "output": "zhang:4\nli:4\nsun:2"}], _generated_cases([(10, ("zhang", "li", "sun", "zhang", "li", "zhang", "sun", "li", "zhang", "li")), (5, ("zhang", "zhang", "zhang", "li", "sun")), (3, ("unknown", "li", "sun")), (0, ()), (6, ("sun", "sun", "sun", "li", "li", "zhang"))], lambda n, names: f"{n} " + " ".join(names), lambda n, names: _votes(*names)), ["结构体", "字符串", "统计"])
