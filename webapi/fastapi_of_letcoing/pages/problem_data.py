PROBLEMS = {
    1001: {
        "id": 1001, "title": "两数之和", "difficulty": "简单", "tags": ["数组", "哈希表"],
        "description": "给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。\n\n你可以假设每种输入只会对应一个答案，并且你不能使用两次相同的元素。",
        "inputFormat": "第一行包含两个整数 n 和 target，分别表示数组长度和目标值。\n第二行包含 n 个整数，表示数组 nums。",
        "outputFormat": "输出两个整数，表示两个数的下标（从 0 开始），用空格分隔。",
        "samples": [
            {"input": "4 9\n2 7 11 15", "output": "0 1"},
            {"input": "3 6\n3 2 4", "output": "1 2"},
        ],
        "testCases": [
            {"input": "5 10\n1 3 5 7 9", "output": "2 4"},
            {"input": "4 0\n0 2 4 6", "output": "0 0"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1002: {
        "id": 1002, "title": "反转字符串", "difficulty": "简单", "tags": ["字符串", "双指针"],
        "description": "编写一个函数，其作用是将输入的字符串反转过来。输入字符串以字符数组的形式给出。\n\n不要给另外的数组分配额外的空间，你必须原地修改输入数组。",
        "inputFormat": "一行字符串 s，只包含可打印 ASCII 字符。",
        "outputFormat": "输出反转后的字符串。",
        "samples": [
            {"input": "hello", "output": "olleh"},
            {"input": "A man", "output": "nam A"},
        ],
        "testCases": [
            {"input": "abc123", "output": "321cba"},
            {"input": "x", "output": "x"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1003: {
        "id": 1003, "title": "斐波那契数列", "difficulty": "简单", "tags": ["递归", "动态规划"],
        "description": "斐波那契数列的定义如下：\nF(0) = 0, F(1) = 1\nF(n) = F(n-1) + F(n-2)（n ≥ 2）\n\n给定 n，请计算 F(n)。",
        "inputFormat": "一个整数 n（0 ≤ n ≤ 30）。",
        "outputFormat": "输出 F(n) 的值。",
        "samples": [
            {"input": "4", "output": "3"},
            {"input": "10", "output": "55"},
        ],
        "testCases": [
            {"input": "0", "output": "0"},
            {"input": "20", "output": "6765"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },

}
