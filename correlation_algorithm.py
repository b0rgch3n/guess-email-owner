# -*- coding: utf-8 -*-

import re
import unicodedata

NON_WORD_CHARACTER_REGEX = re.compile('\W+')


class Storager(object):

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
    has_any_match = False
    storager = Storager()
    for email in email_list:
        # 取邮箱姓名部分并去符号
        email_name = email.split('@')[0]
        email_name = NON_WORD_CHARACTER_REGEX.subn('', email_name)[0]

        # 匹配全名以及全名截断
        best_author_feature_weight = 0
        for author in author_list:
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
            author_feature_match_result = re.findall(author_feature_regex_str, email_name, re.IGNORECASE)
            # 获取权重
            current_author_feature_weight = len(author_feature_match_result)

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print(author_feature_list)
                print(author_feature_regex_str)
                print(author_feature_match_result)
                print(current_author_feature_weight)
            # - - - - - 打印调试日志 - - - - -

            # 判断权重非零并选择最优权重
            is_not_zero_weight = current_author_feature_weight != 0
            is_best_weight = current_author_feature_weight > best_author_feature_weight
            if is_not_zero_weight and is_best_weight:
                storager.update(email=email,
                                name=author,
                                name_weight=current_author_feature_weight)
                has_any_match = True
                print("[+] %(option)s e-mail '%(email)s' author '%(author)s'." %
                      {'option': 'Fount' if best_author_feature_weight == 0 else 'Update', 'email': email,
                       'author': author})
                # 更新最优权重
                best_author_feature_weight = current_author_feature_weight

        # 名字单词匹配有结果则不再进行名字首字母匹配
        if has_any_match is True:
            break

        # 匹配姓名首字母
        for author in author_list:
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
            author_first_char_match_result = re.findall(author_first_char_regex_str, email_name,
                                                        re.IGNORECASE)
            # 获取权重
            current_author_first_char_weight = len(author_first_char_match_result)

            # - - - - - 打印调试日志 - - - - -
            if debug:
                print(author_first_char_list)
                print(author_first_char_regex_str)
                print(author_first_char_match_result)
                print(current_author_first_char_weight)
            # - - - - - 打印调试日志 - - - - -

            # 判断权重非零并选择最优权重
            is_not_zero_weight = current_author_first_char_weight != 0
            if is_not_zero_weight:
                # 获取匹配到的最长字符串的长度
                match_result_len_list = [len(result) for result in author_first_char_match_result]
                longest_match_result_len = max(match_result_len_list)
                # 连续两个以上的字符命中或命中数量等于单词首字母数量时视为匹配
                if longest_match_result_len >= 2 \
                        or current_author_first_char_weight == len(author_first_char_list):
                    storager.update(email=email,
                                    name=author,
                                    name_weight=current_author_first_char_weight)
                    has_any_match = True
                    print("[+] Fount e-mail '%(email)s' author '%(author)s'." %
                          {'email': email, 'author': author})

    # 返回匹配结果
    return storager.email_owners


if __name__ == '__main__':
    pass
