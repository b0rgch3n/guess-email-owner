# -*- coding: utf-8 -*-

import re
import unicodedata

NON_WORD_CHARACTER_REGEX = re.compile('[^A-Za-z]')


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


def correlation(email_list: list, author_list: list, debug=False):
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
        email_user = NON_WORD_CHARACTER_REGEX.subn('', email_user)[0]

        best_author_feature_weight = 0
        for author in author_list:
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

            # # = = = = = 匹配名字每个词前n字母组合（n小段连续字母） = = = = =

            #  e.g. Name:  Yasuhiro KAWAI
            #       Email: kaya@nih.go.jp

            author_feature_shout_list = []
            for limit in [3, 2]:
                author_feature_shout_same_limit = []
                for author_words in author_words_list:
                    if len(author_words) >= limit:
                        author_words_top_n_char = author_words[0:limit]
                        if author_words_top_n_char not in author_feature_list:
                            author_feature_shout_same_limit.append(author_words_top_n_char)
                # 正序和倒序
                author_feature_shout_list.append(''.join(author_feature_shout_same_limit))
                author_feature_shout_list.append(''.join(author_feature_shout_same_limit[::-1]))
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

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print('- ' * 20)
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

            # = = = = = 匹配姓名首字母（不连续字母） = = = = =

            # 将名字切割为单词构造名字单词列表
            author_words_list = NON_WORD_CHARACTER_REGEX.split(author)
            # 除去单字符单词，获取单词首字母，构造名字首字母列表以及对应的正则
            author_first_char_list = [
                author_words[0] for author_words in author_words_list
                if len(author_words) > 0  # 避免出现空字符串的情况
            ]
            # author_first_char_regex_str = '[' + ''.join(author_first_char_list) + ']+'
            author_first_char_regex_str = '|'.join(author_first_char_list)
            # 匹配名字首字母
            author_first_char_match_result = re.findall(author_first_char_regex_str, email_user_copy,
                                                        re.IGNORECASE)

            author_first_char_match_count = len(author_first_char_match_result)
            # 获取权重（按字母数计算）
            current_author_first_char_weight = author_first_char_match_count
            # 首字母不连续，应弱化权重
            current_author_first_char_weight = 0.8 * current_author_first_char_weight
            # 条件1：邮箱姓名部分只由首字母组成
            con1 = len(author) == author_first_char_match_count
            # 条件2：前面2中情况已经有匹配到
            con2 = current_author_weight > 0
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
                print('= ' * 20)

            # 权重必须 > 0.8 才进行权重更新操作
            if current_author_weight <= 0.8:
                continue

            # 判断权重非零并选择最优权重
            is_not_zero_weight = current_author_weight != 0
            is_best_weight = current_author_weight > best_author_feature_weight
            if is_not_zero_weight and is_best_weight:
                storager.update(email=email,
                                name=author,
                                name_weight=current_author_weight)
                print("[+] %(option)s e-mail '%(email)s' author '%(author)s'." % {
                    'option': 'Fount' if best_author_feature_weight == 0 else 'Update',
                    'email': email,
                    'author': author
                })
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
        'tkunieda@okayama-u.ac.jp'
    ]
    author_list = [
        ' ',
        'Kazuhiro Yoneda',
        'Yasuhiro KAWAI',
        'Takashi HIRANO',
        'Yasuhiro KAWAI',
        'Taishi KANII',
        'Tetsuo KUNIEDA',
    ]
    result = correlation(email_list=email_list, author_list=author_list, debug=True)
    print(json.dumps(result, ensure_ascii=False, indent=True))
