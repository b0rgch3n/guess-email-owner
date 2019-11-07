# -*- coding: utf-8 -*-

import re
import itertools
import unicodedata

NON_ALPHABET_CHARACTER_REGEX = re.compile('[^A-Za-z]')
NON_WORD_CHARACTER_REGEX = re.compile('\W+')


class Storager(object):
    """
        用于存储邮箱和姓名匹配结果的数据结构
    """

    def __init__(self):
        self.__owners_map = {}

    def update(self, email, name=None, name_weight=None):

        # 设置权重默认值
        if name_weight is None:
            name_weight = 1

        # 检查 email 是否已收录
        owner = self.__owners_map.get(email, None)
        if owner is not None:
            # 存在则更新 owner 对象
            owner.set_name(name=name, name_weight=name_weight)
        else:
            # 不存在则新增 owner 对象
            owner = Owner()
            owner.set_name(name=name, name_weight=name_weight)
            self.__owners_map.setdefault(email, owner)

    @property
    def email_owners(self):
        email_owners = {
            email: owner.name
            for email, owner in self.__owners_map.items()
        }
        return email_owners


class Owner(object):
    """
        用于存储权重的数据结构
    """

    def __init__(self):
        self.__name = None
        self.__name_weight = 0

    def set_name(self, name, name_weight):
        if name is not None:
            if self.__name is None:
                self.__name = name
            elif self.__name is not None and name_weight > self.__name_weight:
                self.__name = name
                self.__name_weight = name_weight

    @property
    def name(self):
        return self.__name


def correlation(email_list: list, author_list: list, keep_original=False, debug=False):
    """
        匹配邮箱对应的名字
    :param email_list:  邮箱列表
    :param author_list: 姓名列表
    :param debug:       是否打印调试
    :return:            匹配邮箱对应名字结果
    """

    # 检查参数
    email_list = [
        email for email in email_list if '@' in email
    ]
    author_list = [
        author for author in author_list if author.strip() != ''
    ]

    storager = Storager()
    for email in email_list:
        # 取邮箱姓名部分并去符号
        email_user = email.split('@')[0]
        email_user = NON_ALPHABET_CHARACTER_REGEX.subn('', email_user)[0]

        best_author_feature_weight = 0
        for author in author_list:

            # 标记 TOP 3 算法是否有匹配结果
            correlation_1_done = False
            correlation_2_done = False
            correlation_3_done = False

            # 暂时保存原始姓名
            original_author_name = author

            # 初始化但前权重
            current_author_weight = 0

            # 复制邮箱姓名部分副本
            email_user_copy = ''.join(email_user)

            # = = = = = 匹配全名以及全名截断（连续字母） = = = = =

            # 去除小语种音调
            author = unicodedata.normalize('NFKD', author).encode('ascii', 'ignore').decode()
            # 将名字切割为单词构造名字单词列表
            author_words_list = NON_WORD_CHARACTER_REGEX.split(author)
            # 除去单字符单词，构造名字特征列表以及对应的正则
            author_feature_list = [
                author_words for author_words in author_words_list if len(author_words) > 1
            ]
            # 对名字单词进行截断（最小长度4位）
            upper_limit = max(list(map(lambda w: len(w), author_words_list)))
            lower_limit = 4
            for limit in range(upper_limit, lower_limit - 1, -1):
                for author_words in author_words_list:
                    if len(author_words) >= limit:
                        author_words_top_n_char = author_words[0:limit]
                        if author_words_top_n_char not in author_feature_list:
                            author_feature_list.append(author_words_top_n_char)
            author_feature_regex_str = '|'.join(author_feature_list)
            # 匹配名字单词特征
            author_feature_match_result = re.findall(author_feature_regex_str, email_user_copy, re.IGNORECASE)
            # 获取权重（按字母数计算）
            current_author_feature_weight = sum([
                len(author_feature) for author_feature in author_feature_match_result
            ])
            # 名字单词字母连续，应强化权重
            current_author_feature_weight = 1.2 * current_author_feature_weight
            current_author_weight += current_author_feature_weight

            # 有结果时标记
            if current_author_feature_weight != 0:
                correlation_1_done = True

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print('= ' * 20)
                print('Name: ', author)
                print('Email:', email)
                print('User Part:', email_user_copy)
                print(author_feature_list)
                print(author_feature_regex_str)
                print(author_feature_match_result)
                print(current_author_feature_weight)
            # - - - - - 打印调试日志 - - - - -

            # 删除匹配到的内容，避免重复匹配
            for author_feature in author_feature_match_result:
                email_user_copy = email_user_copy.replace(author_feature, '')

            # = = = = = 匹配全名以及全名截断的倒序情况（连续字母） = = = = =

            # 对所有名字单词截断进行反转
            # 目的是为了识别故意将名字部分倒转的情况
            #  e.g. Name:  Kazuhiro Yoneda
            #       Email: dradenoy@ybb.ne.jp

            author_feature_reverse_list = [
                author_feature[::-1] for author_feature in author_feature_list
            ]
            author_feature_reverse_regex_str = '|'.join(author_feature_reverse_list)
            # 匹配名字单词特征
            author_feature_reverse_match_result = re.findall(author_feature_reverse_regex_str, email_user_copy,
                                                             re.IGNORECASE)
            # 获取权重（按字母数计算）
            current_author_feature_reverse_weight = sum([
                len(author_feature_reverse) for author_feature_reverse in author_feature_reverse_match_result
            ])
            # 名字单词字母连续，应强化权重
            current_author_feature_reverse_weight = 1.2 * current_author_feature_reverse_weight
            current_author_weight += current_author_feature_reverse_weight

            # 有结果时标记
            if current_author_feature_reverse_weight != 0:
                correlation_2_done = True

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print('- ' * 20)
                print('Name: ', author)
                print('Email:', email)
                print('User Part:', email_user_copy)
                print(author_feature_reverse_list)
                print(author_feature_reverse_regex_str)
                print(author_feature_reverse_match_result)
                print(current_author_feature_reverse_weight)
            # - - - - - 打印调试日志 - - - - -

            # 删除匹配到的内容，避免重复匹配
            for author_feature_reverse in author_feature_reverse_match_result:
                email_user_copy = email_user_copy.replace(author_feature_reverse, '')

            # # = = = = = 匹配名字每个词前n字母组合（n小段连续字母，每段都由单词的前 2～3 个字母组成） = = = = =

            #  e.g. Name:  Yasuhiro KAWAI
            #       Email: kaya@nih.go.jp

            # 取出所有单词的前 2～3 个字母
            author_feature_shout_same_limit_matrix = [[] for _ in author_words_list]
            author_feature_shout_list = []
            for limit in [3, 2]:
                # author_feature_shout_same_limit = []
                for index, author_words in enumerate(author_words_list):
                    if len(author_words) >= limit:
                        author_words_top_n_char = author_words[0:limit]
                        if author_words_top_n_char not in author_feature_list:
                            # author_feature_shout_same_limit.append(author_words_top_n_char)
                            author_feature_shout_same_limit_matrix[index].append(author_words_top_n_char)

            # 清除空行，避免影响递归
            author_feature_shout_same_limit_matrix = [
                row for row in author_feature_shout_same_limit_matrix if len(row) != 0
            ]

            # 通过递归计算所有片段可能存在的组合
            author_feature_shout_matrix = []

            # 生成矩阵首行元素到末行元素之间所有可能的路径
            def generate_path(matrix, **kwargs):
                word_list = kwargs.get('word_list', list())
                depth = kwargs.get('depth', 0)
                # 递归深度在矩阵行数之内
                if depth >= len(matrix):
                    author_feature_shout_matrix.append(word_list)
                    return
                for row in matrix[depth]:
                    generate_path(matrix=matrix, word_list=[*word_list, row], depth=depth + 1)

            # 调用递归
            generate_path(author_feature_shout_same_limit_matrix)

            for author_feature_shout_row in author_feature_shout_matrix:
                # print(author_feature_shout_row)
                author_feature_shout_same_count = len(author_feature_shout_row)
                # 词汇量过多可能造成内存暴涨，因此超过五个时统统跳过
                if author_feature_shout_same_count > 5:
                    continue
                for count in range(2, author_feature_shout_same_count + 1):
                    for permutations in itertools.permutations(author_feature_shout_row, count):
                        author_feature_shout_list.append(''.join(permutations))

            # 去重排序
            author_feature_shout_list = list(set(author_feature_shout_list))
            author_feature_shout_list = sorted(author_feature_shout_list, key=lambda i: len(i), reverse=True)

            author_feature_shout_regex_str = '|'.join(author_feature_shout_list)
            # 匹配名字单词特征
            author_feature_shout_match_result = re.findall(author_feature_shout_regex_str, email_user_copy,
                                                           re.IGNORECASE)
            # 获取权重（按字母数计算）
            current_author_feature_shout_weight = sum([
                len(author_feature_shout) for author_feature_shout in author_feature_shout_match_result
            ])
            # 权重不变化
            current_author_feature_shout_weight = 1.0 * current_author_feature_shout_weight
            current_author_weight += current_author_feature_shout_weight

            # 有结果时标记
            if current_author_feature_shout_weight != 0:
                correlation_3_done = True

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print('= ' * 20)
                print('Name: ', author)
                print('Email:', email)
                print('User Part:', email_user_copy)
                print(author_feature_shout_list)
                print(author_feature_shout_regex_str)
                print(author_feature_shout_match_result)
                print(current_author_feature_shout_weight)
            # - - - - - 打印调试日志 - - - - -

            # 删除匹配到的内容，避免重复匹配
            for author_feature_shout in author_feature_shout_match_result:
                email_user_copy = email_user_copy.replace(author_feature_shout, '')

            # = = = = = 匹配姓名首字母（连续字母，需要名字和邮箱的顺序恰好一致） = = = = =
            #  e.g. Name:  Reginald Q Knight
            #       Email: rqkspine1@aol.com
            #  e.g. Name:  Taniya Bardhan
            #       Email: tb1@nibmg.ac.in
            #  e.g. Name:  Bornali Bhattacharjee
            #       Email: bb2@nibmg.ac.in

            # 将名字切割为单词构造名字单词列表
            author_words_list = NON_WORD_CHARACTER_REGEX.split(author)
            # 除去单字符单词，获取单词首字母，构造名字首字母列表以及对应的正则
            author_first_char_list = [
                author_words[0] for author_words in author_words_list
                if len(author_words) > 0  # 避免出现空字符串的情况
            ]
            author_first_char_con_regex_str = ''.join(author_first_char_list)
            # 匹配名字首字母
            author_first_char_con_match = re.search(author_first_char_con_regex_str,
                                                    email_user_copy,
                                                    re.IGNORECASE)
            if author_first_char_con_match is not None:
                author_first_char_con_match_result = author_first_char_con_match.group()
                author_first_char_match_count = len(author_first_char_con_match_result)
                # 获取权重（按字母数计算）
                current_author_first_char_weight = author_first_char_match_count
                # 此处为首字母连续，也应弱化权重
                current_author_first_char_weight = 0.85 * current_author_first_char_weight
                # 条件1：邮箱姓名部分只由首字母组成
                con1 = len(email_user) == author_first_char_match_count
                # 条件2：前面没有任何有匹配到情况
                con2 = not (correlation_1_done or correlation_2_done or correlation_3_done)
                # 满足以上任意一种则参与权重计算
                if con1 or con2:
                    current_author_weight += current_author_first_char_weight

                # - - - - - 打印调试日志 - - - - -
                if debug:
                    print('- ' * 20)
                    print('Name: ', author)
                    print('Email:', email)
                    print('User Part:', email_user_copy)
                    print(author_first_char_list)
                    print(author_first_char_con_regex_str)
                    print(author_first_char_con_match_result)
                    print(current_author_first_char_weight)
                # - - - - - 打印调试日志 - - - - -

                if debug:
                    print('- ' * 20)
                    print('weight: ', current_author_weight)

            # = = = = = 匹配姓名首字母（不连续字母） = = = = =

            # 将名字切割为单词构造名字单词列表
            author_words_list = NON_WORD_CHARACTER_REGEX.split(author)
            # 除去单字符单词，获取单词首字母，构造名字首字母列表以及对应的正则
            author_first_char_list = [
                author_words[0] for author_words in author_words_list
                if len(author_words) > 0  # 避免出现空字符串的情况
            ]
            author_first_char_regex_str = '|'.join(author_first_char_list)
            # 匹配名字首字母
            author_first_char_match_result = re.findall(author_first_char_regex_str, email_user_copy,
                                                        re.IGNORECASE)
            # 忽略单字母多次出现
            author_first_char_match_result = list(set(author_first_char_match_result))
            author_first_char_match_count = len(author_first_char_match_result)

            # 获取权重（按字母数计算）
            current_author_first_char_weight = author_first_char_match_count
            # 首字母不连续，应弱化权重
            current_author_first_char_weight = 0.8 * current_author_first_char_weight
            # 条件1：邮箱姓名部分只由首字母组成
            con1 = len(email_user) == author_first_char_match_count
            # 条件2：前面有已经有匹配到的情况（因为首字母不联系的情况可能很不准确）
            con2 = correlation_1_done or correlation_2_done or correlation_3_done
            # 满足以上任意一种则参与权重计算
            if con1 or con2:
                current_author_weight += current_author_first_char_weight

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print('- ' * 20)
                print('Name: ', author)
                print('Email:', email)
                print('User Part:', email_user_copy)
                print(author_first_char_list)
                print(author_first_char_regex_str)
                print(author_first_char_match_result)
                print(current_author_first_char_weight)
            # - - - - - 打印调试日志 - - - - -

            if debug:
                print('- ' * 20)
                print('weight: ', current_author_weight)

            # 权重必须 > 0.8 才进行权重更新操作
            if current_author_weight <= 0.8:
                continue

            # 判断权重非零并选择最优权重
            is_not_zero_weight = current_author_weight != 0
            is_best_weight = current_author_weight > best_author_feature_weight
            if is_not_zero_weight and is_best_weight:
                name = original_author_name if keep_original else author
                storager.update(email=email,
                                name=name,
                                name_weight=current_author_weight)
                print("[+] %(option)s e-mail '%(email)s' author '%(author)s'." %
                      {'option': 'Fount' if best_author_feature_weight == 0 else 'Update', 'email': email,
                       'author': name})
                # 更新最优权重
                best_author_feature_weight = current_author_weight

    # 返回匹配结果
    return storager.email_owners


if __name__ == '__main__':
    import json

    email_list = [
        'dradenoy@ybb.ne.jp',
        't3hirano@nodai.ac.jp',
        'kaya@nih.go.jp',
        'tkunieda@okayama-u.ac.jp',
        'rqkspine1@aol.com',
        "tb1@nibmg.ac.in",
        "bb2@nibmg.ac.in",
        "marbu@unam.mx",

        "alydan@hotmail.com",
        "acmusa23@yahoo.com.br",
        "rafaelquadros13@hotmail.com",
        "michelli_quimifarm@yahoo.com.br",
        "rogeriosst@gmail.com",
        "jrvieira@ufpa.br",
        "percario@ufpa.br",
        "spercario49@gmail.com",

        'poda@mail.med.upenn.edu',
    ]
    author_list = [
        ' ',
        'Reginald Q Knight',
        "Taniya Bardhan",
        "Bornali Bhattacharjee",
        'Kazuhiro Yoneda',
        'Yasuhiro KAWAI',
        'Takashi HIRANO',
        'Yasuhiro KAWAI',
        'Taishi KANII',
        'Tetsuo KUNIEDA',
        "Martha Irene Bucio Torres",
        "PAZ MAR&IACUTE",

        "Danilo Reymão Moreira",
        "Ana Carolina Musa Gonçalves Uberti",
        "Antonio Rafael Quadros Gomes",
        "Michelli Erica Souza Ferreira",
        "Rogério Silva Santos",
        "Michael Dean Green",
        "José Ricardo dos Santos Vieira",
        "Maria Fani Dolabela",
        "Sandro Percário",

        'Daniel J. Powell'
    ]
    result = correlation(email_list=email_list, author_list=author_list, debug=False)
    print(json.dumps(result, ensure_ascii=False, indent=True))
