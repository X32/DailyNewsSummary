"""
单元测试文件：测试 crawler.py 中的 get_news 函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from bs4 import BeautifulSoup


class TestGetNews:
    """测试 get_news 函数"""

    @pytest.fixture
    def mock_news_class(self):
        """模拟 News 类"""
        with patch('crawler.News') as mock:
            yield mock

    @pytest.fixture
    def mock_insert_news(self):
        """模拟 insert_news 函数"""
        with patch('crawler.insert_news') as mock:
            yield mock

    @pytest.fixture
    def mock_html(self):
        """模拟全局 html 变量"""
        from bs4 import BeautifulSoup
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
                <li><a href="http://example.com/news1">新闻标题1</a></li>
                <li><a href="http://example.com/news2">新闻标题2</a></li>
                <li><a href="http://example.com/news3">新闻标题3</a></li>
            </ul>
        """, 'lxml')
        return html

    @pytest.fixture
    def mock_html_empty_list(self):
        """模拟没有 li 元素的 html"""
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
            </ul>
        """, 'lxml')
        return html

    @pytest.fixture
    def mock_html_no_ul(self):
        """模拟找不到 ul 元素的 html"""
        html = BeautifulSoup("""
            <div id="test_id" class="list_14_noBg" data-client="p_china">
            </div>
        """, 'lxml')
        return html

    @pytest.fixture
    def mock_html_missing_href(self):
        """模拟 a 标签缺少 href 属性的 html"""
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
                <li><a>新闻标题1</a></li>
            </ul>
        """, 'lxml')
        return html

    @pytest.fixture
    def mock_html_no_a_tag(self):
        """模拟 li 中没有 a 标签的 html"""
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
                <li>新闻标题1</li>
            </ul>
        ""', 'lxml')
        return html

    def test_get_news_normal_case(self, mock_news_class, mock_insert_news):
        """
        测试正常情况：正确提取新闻信息并调用 insert_news
        """
        # 导入模块前先设置全局 mock
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
                <li><a href="http://example.com/news1">新闻标题1</a></li>
                <li><a href="http://example.com/news2">新闻标题2</a></li>
            </ul>
        """, 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_china")

            # 验证 News 类被调用 2 次（每条新闻一次）
            assert mock_news_class.call_count == 2

            # 验证第一次调用
            first_call = mock_news_class.call_args_list[0]
            assert first_call.kwargs['category'] == 'china'
            assert first_call.kwargs['headline'] == '新闻标题1'
            assert first_call.kwargs['hyperlink'] == 'http://example.com/news1'
            assert isinstance(first_call.kwargs['createtime'], datetime)

            # 验证第二次调用
            second_call = mock_news_class.call_args_list[1]
            assert second_call.kwargs['category'] == 'china'
            assert second_call.kwargs['headline'] == '新闻标题2'
            assert second_call.kwargs['hyperlink'] == 'http://example.com/news2'
            assert isinstance(second_call.kwargs['createtime'], datetime)

            # 验证 insert_news 被调用 2 次
            assert mock_insert_news.call_count == 2

    def test_get_news_with_empty_li_list(self, mock_news_class, mock_insert_news):
        """
        测试边界情况：找到 ul 元素但没有 li 元素
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_world">
            </ul>
        """, 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_world")

            # 验证 News 类没有被调用
            assert mock_news_class.call_count == 0

            # 验证 insert_news 没有被调用
            assert mock_insert_news.call_count == 0

    def test_get_news_with_ul_not_found(self, mock_news_class, mock_insert_news):
        """
        测试异常情况：找不到指定 id 的 ul 元素
        """
        html = BeautifulSoup("""
            <div id="other_id" class="list_14_noBg" data-client="p_finance">
            </div>
        """, 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_finance")

            # 验证 News 类没有被调用
            assert mock_news_class.call_count == 0

            # 验证 insert_news 没有被调用
            assert mock_insert_news.call_count == 0

    def test_get_news_with_type_length_2(self, mock_news_class, mock_insert_news):
        """
        测试边界情况：type 参数长度为 2（type[2:] 返回空字符串）
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="ab">
                <li><a href="http://example.com/news1">新闻标题1</a></li>
            </ul>
        ""', 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "ab")

            # 验证 News 类被调用，category 为空字符串
            assert mock_news_class.call_count == 1
            call_args = mock_news_class.call_args_list[0]
            assert call_args.kwargs['category'] == ''

            # 验证 insert_news 被调用
            assert mock_insert_news.call_count == 1

    def test_get_news_with_missing_href(self, mock_news_class, mock_insert_news):
        """
        测试异常情况：a 标签缺少 href 属性
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_ent">
                <li><a>新闻标题1</a></li>
            </ul>
        ""', 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_ent")

            # 验证 News 类被调用，hyperlink 为 None
            assert mock_news_class.call_count == 1
            call_args = mock_news_class.call_args_list[0]
            assert call_args.kwargs['headline'] == '新闻标题1'
            assert call_args.kwargs['hyperlink'] is None
            assert call_args.kwargs['category'] == 'ent'

            # 验证 insert_news 被调用
            assert mock_insert_news.call_count == 1

    def test_get_news_with_no_a_tag(self, mock_news_class, mock_insert_news):
        """
        测试异常情况：li 中没有 a 标签
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_tech">
                <li>新闻标题1</li>
            </ul>
        ""', 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数 - 这会抛出 AttributeError
            with pytest.raises(AttributeError):
                get_news("test_id", "p_tech")

            # 验证 News 类没有被调用
            assert mock_news_class.call_count == 0

            # 验证 insert_news 没有被调用
            assert mock_insert_news.call_count == 0

    def test_get_news_with_empty_headline(self, mock_news_class, mock_insert_news):
        """
        测试边界情况：新闻标题为空
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_sports">
                <li><a href="http://example.com/news1"></a></li>
            </ul>
        ""', 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_sports")

            # 验证 News 类被调用，headline 为空字符串
            assert mock_news_class.call_count == 1
            call_args = mock_news_class.call_args_list[0]
            assert call_args.kwargs['headline'] == ''
            assert call_args.kwargs['hyperlink'] == 'http://example.com/news1'
            assert call_args.kwargs['category'] == 'sports'

            # 验证 insert_news 被调用
            assert mock_insert_news.call_count == 1

    def test_get_news_with_multiple_li(self, mock_news_class, mock_insert_news):
        """
        测试正常情况：多个 li 元素
        """
        html = BeautifulSoup("""
            <ul id="test_id" class="list_14_noBg" data-client="p_china">
                <li><a href="http://example.com/news1">新闻1</a></li>
                <li><a href="http://example.com/news2">新闻2</a></li>
                <li><a href="http://example.com/news3">新闻3</a></li>
                <li><a href="http://example.com/news4">新闻4</a></li>
                <li><a href="http://example.com/news5">新闻5</a></li>
            </ul>
        """, 'lxml')

        with patch('crawler.html', html):
            from crawler import get_news

            # 调用函数
            get_news("test_id", "p_china")

            # 验证 News 类被调用 5 次
            assert mock_news_class.call_count == 5

            # 验证每条新闻的 category 都正确
            for call in mock_news_class.call_args_list:
                assert call.kwargs['category'] == 'china'

            # 验证 insert_news 被调用 5 次
            assert mock_insert_news.call_count == 5

    def test_get_news_with_different_type_values(self, mock_news_class, mock_insert_news):
        """
        测试不同 type 参数值下的 category 提取
        """
        test_cases = [
            ("p_china", "china"),
            ("p_world", "world"),
            ("p_finance", "finance"),
            ("p_ent", "ent"),
            ("p_tech", "tech"),
            ("p_sports", "sports"),
            ("abc_xyz", "c_xyz"),  # 测试非标准格式
        ]

        for type_value, expected_category in test_cases:
            html = BeautifulSoup(f"""
                <ul id="test_id" class="list_14_noBg" data-client="{type_value}">
                    <li><a href="http://example.com/news">新闻标题</a></li>
                </ul>
            """, 'lxml')

            with patch('crawler.html', html):
                from crawler import get_news

                # 重置 mock
                mock_news_class.reset_mock()
                mock_insert_news.reset_mock()

                # 调用函数
                get_news("test_id", type_value)

                # 验证 category 正确提取
                assert mock_news_class.call_count == 1
                call_args = mock_news_class.call_args_list[0]
                assert call_args.kwargs['category'] == expected_category
