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
    1004: {
        "id": 1004, "title": "有效括号匹配", "difficulty": "中等", "tags": ["栈", "字符串"],
        "description": "给定一个只包括 '('、')'、'{'、'}'、'['、']' 的字符串 s，判断字符串是否有效。\n\n有效字符串需满足：\n1. 左括号必须用相同类型的右括号闭合。\n2. 左括号必须以正确的顺序闭合。",
        "inputFormat": "一行字符串 s，只包含括号字符。",
        "outputFormat": "输出 true 或 false。",
        "samples": [
            {"input": "()", "output": "true"},
            {"input": "()[]{}", "output": "true"},
        ],
        "testCases": [
            {"input": "(]", "output": "false"},
            {"input": "([)]", "output": "false"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1005: {
        "id": 1005, "title": "链表中间节点", "difficulty": "中等", "tags": ["链表", "快慢指针"],
        "description": "给定一个头结点为 head 的非空单链表，返回链表的中间结点。\n\n如果有两个中间结点，则返回第二个中间结点。\n\n输入格式：第一行 n 表示链表长度，第二行 n 个整数表示链表元素。",
        "inputFormat": "第一行一个整数 n。\n第二行 n 个整数，表示链表元素。",
        "outputFormat": "输出中间节点的值。",
        "samples": [
            {"input": "5\n1 2 3 4 5", "output": "3"},
            {"input": "6\n1 2 3 4 5 6", "output": "4"},
        ],
        "testCases": [
            {"input": "1\n42", "output": "42"},
            {"input": "4\n10 20 30 40", "output": "30"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1006: {
        "id": 1006, "title": "合并区间", "difficulty": "中等", "tags": ["排序", "数组"],
        "description": "以数组 intervals 表示若干个区间的集合，其中单个区间为 intervals[i] = [starti, endi]。请你合并所有重叠的区间，并返回一个不重叠的区间数组。\n\n输入格式：第一行 n 表示区间个数，接下来 n 行每行两个整数 start 和 end。",
        "inputFormat": "第一行一个整数 n。\n接下来 n 行，每行两个整数 start 和 end。",
        "outputFormat": "输出合并后的区间，每行一个 [start, end]。",
        "samples": [
            {"input": "4\n1 3\n2 6\n8 10\n15 18", "output": "1 6\n8 10\n15 18"},
            {"input": "2\n1 4\n4 5", "output": "1 5"},
        ],
        "testCases": [
            {"input": "2\n1 4\n0 4", "output": "0 4"},
            {"input": "1\n5 7", "output": "5 7"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1007: {
        "id": 1007, "title": "K 个一组翻转链表", "difficulty": "困难", "tags": ["链表", "递归"],
        "description": "给你链表的头节点 head，每 k 个节点一组进行翻转，请你返回修改后的链表。\n\nk 是一个正整数，它的值小于或等于链表的长度。如果节点总数不是 k 的整数倍，那么请将最后剩余的节点保持原有顺序。",
        "inputFormat": "第一行两个整数 n 和 k，分别表示链表长度和每组大小。\n第二行 n 个整数，表示链表元素。",
        "outputFormat": "输出翻转后的链表元素，用空格分隔。",
        "samples": [
            {"input": "5 2\n1 2 3 4 5", "output": "2 1 4 3 5"},
            {"input": "5 3\n1 2 3 4 5", "output": "3 2 1 4 5"},
        ],
        "testCases": [
            {"input": "1 1\n99", "output": "99"},
            {"input": "4 4\n1 2 3 4", "output": "4 3 2 1"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1008: {
        "id": 1008, "title": "最长回文子串", "difficulty": "中等", "tags": ["字符串", "动态规划"],
        "description": "给你一个字符串 s，找到 s 中最长的回文子串。\n\n如果字符串的反序与原始字符串相同，则该字符串称为回文字符串。",
        "inputFormat": "一行字符串 s，只包含小写英文字母。",
        "outputFormat": "输出最长回文子串。如果有多个，返回最先出现的。",
        "samples": [
            {"input": "babad", "output": "bab"},
            {"input": "cbbd", "output": "bb"},
        ],
        "testCases": [
            {"input": "a", "output": "a"},
            {"input": "ac", "output": "a"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1009: {
        "id": 1009, "title": "接雨水", "difficulty": "困难", "tags": ["栈", "数组", "双指针"],
        "description": "给定 n 个非负整数表示每个宽度为 1 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。",
        "inputFormat": "第一行一个整数 n。\n第二行 n 个非负整数，表示柱子的高度。",
        "outputFormat": "输出能接的雨水总量。",
        "samples": [
            {"input": "12\n0 1 0 2 1 0 1 3 2 1 2 1", "output": "6"},
            {"input": "3\n4 2 3", "output": "1"},
        ],
        "testCases": [
            {"input": "1\n0", "output": "0"},
            {"input": "4\n3 0 0 2", "output": "4"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
    1010: {
        "id": 1010, "title": "单词搜索", "difficulty": "中等", "tags": ["回溯", "矩阵"],
        "description": "给定一个 m x n 二维字符网格 board 和一个字符串单词 word。如果 word 存在于网格中，返回 true；否则，返回 false。\n\n单词必须按照字母顺序，通过相邻的单元格内的字母构成。\n\n输入格式：第一行 m n\n接下来 m 行，每行 n 个字符（小写字母）\n最后一行是单词 word",
        "inputFormat": "第一行两个整数 m 和 n。\n接下来 m 行，每行 n 个小写字母。\n最后一行是待搜索的单词。",
        "outputFormat": "输出 true 或 false。",
        "samples": [
            {"input": "3 4\nABCE\nSFCS\nADEE\nABCCED", "output": "true"},
            {"input": "3 4\nABCE\nSFCS\nADEE\nSEE", "output": "true"},
        ],
        "testCases": [
            {"input": "3 4\nABCE\nSFCS\nADEE\nABCB", "output": "false"},
            {"input": "1 1\nA\nA", "output": "true"},
        ],
        "timeLimit": 1000, "memoryLimit": 256,
    },
}
