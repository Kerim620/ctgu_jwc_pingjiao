import requests
import time
from re import findall
from aip import AipOcr


# 获取验证码
def get_code(s, headers, code_url):
    # 在此替换你自己信息
    APP_ID = 'your app_id'
    API_KEY = 'your api_key'
    SECRET_KEY = 'your secret_key'
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    r = s.get(url=code_url, headers=headers)
    result = client.basicAccurate(r.content)
    temp = result['words_result'][0]['words'].split()
    code = "".join(temp)
    print('验证码已自动识别:' + code)
    return code

# 登陆
def login(s, login_url, headers, captcha, login_data):
    login_data['CheckCode'] = str(captcha)
    r = s.post(url=login_url, data=login_data, headers=headers)


# 获取评教信息页面
def get_page(s, headers, pj_page_url):
    r = s.get(url=pj_page_url, headers=headers)
    return r.text


# 获取课程列表
def courses_list_pattern(html):
    courses_list = r'<td style="height:25px;">.*?</td>\s+'
    courses_list_result = findall(courses_list, html)
    return courses_list_result


# 解析并获取评教信息页面
def course_info_pattern(str):
    course_info = r'<td style="height:25px;">(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?).*?'
    course_info_result = findall(course_info,str)
    return course_info_result[0][6],'【'+course_info_result[0][3]+' '+course_info_result[0][5]+' '+course_info_result[0][6]+'】'


# 1.解析课程未开课或者截止评教了，匹配链接
def step1_pattern(str):
    step1 = r"'Stu_Assess_(.*?)','学生评教"
    step1_result = findall(step1, str)
    return step1_result


# 2.解析已评教，匹配字符串‘已评教’
def step2_pattern(str):
    step2 = r".*?已评教.*?"
    step2_result = findall(step2, str)
    return step2_result


# 解析最终的评教完成页面
def post_course_data_result_pattern(html):
    post_course_data_result = r"<script language='javascript' defer>alert(.*?);</script></form>"
    result = findall(post_course_data_result, html)
    # print(result)
    if result == ["('你的评教结果已被成功保存！请关闭本窗口！')"]:
        state = 1
    else:
        state = 0
    return result


# 解析post需要附带的页面信息
def view_pattern(html):
    view_pattern1 = r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(.*?)" />'
    view_pattern2 = r'<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.*?)" />'
    result1 = findall(view_pattern1, html)
    result2 = findall(view_pattern2, html)
    # print(result1)
    return result1[0], result2[0]


# 获取评教信息页面
def view_page(s, headers, one_page_url):
    r = s.get(url=one_page_url, headers=headers)
    # print(r.text)
    return r.text


# 获取单个评教链接的页面
def post_course_data(s, headers, one_page_url, data):
    # print(data)
    r = s.post(url=one_page_url, headers=headers, data=data)
    return r.text


def main():
    print("-" * 60)
    print('欢迎使用CTGU自动评教脚本，默认全部老师好评，请悉知。', '\n')

    s = requests.Session()
    code_url = 'http://210.42.38.26:84/jwc_glxt/ValidateCode.aspx'  # 验证码地址
    login_url = 'http://210.42.38.26:84/jwc_glxt/Login.aspx'  # 登陆地址
    pj_page_url = 'http://210.42.38.26:84/jwc_glxt/Stu_Assess/Stu_Assess.aspx'  # 评教总页面
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/83.0.4103.7 Safari/537.36 '
    }
    login_data = {
        '__VIEWSTATE': '/wEPDwUKLTQ4NjU1OTA5NGQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFCGJ0bkxvZ2lu87YBxXeCmB2j7CocJsNhyfsKzWE=',
        '__EVENTVALIDATION': '/wEWBQLYts3EAgKl1bKzCQKC3IeGDAK1qbSRCwLO44u1Dfpw4XbGYape7ys17s2u91txfgZM',
        'txtUserName': '',
        'btnLogin.x': '52',
        'btnLogin.y': '17',
        'txtPassword': '',
        'CheckCode': ''
    }
    login_data['txtUserName'] = input('请输入学号，按回车以继续：')
    login_data['txtPassword'] = input('请输入密码，按回车以继续：')

    captcha = get_code(s, headers, code_url)
    login(s, login_url, headers, captcha, login_data)
    pj_html = get_page(s, headers, pj_page_url)
    courses_list = courses_list_pattern(pj_html)
    sum = len(courses_list)
    if sum == 0:
        print('\n登陆失败，请检查密码或验证码后重试!\n')
    else:
        print('\n登陆成功！\n')
    finsh = 0
    finshed = 0
    other = 0
    print('您总共有' + str(sum) + '门课\n')
    print('-' * 60)
    for i in range(len(courses_list)):
        course_info_str = courses_list[i]
        course_type, course_info = course_info_pattern(course_info_str)
        step1_result = step1_pattern(course_info_str)
        step2_result = step2_pattern(course_info_str)
        if len(step2_result) != 0:
            print(course_info + ' 该门课已评教过，本次不评教\n')
            finshed += 1
        else:
            if len(step1_result) == 0:
                print(course_info + ' 该门课未开课或已截止评教\n')
                other += 1
            else:
                print(course_info + ' 该门课正在评教中...')
                course_url = 'http://210.42.38.26:84/jwc_glxt/Stu_Assess/Stu_Assess_' + ''.join(step1_result[0])
                # 这次只是获取评教要带有的部分信息，伪提交
                pj_page_html = view_page(s, headers, course_url)
                __VIEWSTATE, __EVENTVALIDATION = view_pattern(pj_page_html)
                # 定型提交的数据
                if course_type == '理论类':
                    data = {
                        '__VIEWSTATE': '',
                        '__EVENTVALIDATION': '',
                        'GridCourse2$ctl02$userscore': '18',
                        'GridCourse2$ctl03$userscore': '6',
                        'GridCourse2$ctl04$userscore': '10',
                        'GridCourse2$ctl05$userscore': '10',
                        'GridCourse2$ctl06$userscore': '10',
                        'GridCourse2$ctl07$userscore': '6',
                        'GridCourse2$ctl08$userscore': '10',
                        'GridCourse2$ctl09$userscore': '10',
                        'GridCourse2$ctl10$userscore': '10',
                        'GridCourse2$ctl11$userscore': '10',
                        'SuitTeach': 'RadioButton1',
                        'TeacherGood': '',
                        'TeacherChange': '',
                        'TeachForm': 'RadioButton4',
                        'HopeTeachForm': 'RadioButton12',
                        'TeachTool': 'RadioButton8',
                        'btnSave': '·确定·',
                    }
                if course_type == '实践类':
                    data = {
                        '__VIEWSTATE': '',
                        '__EVENTVALIDATION': '',
                        'TextBox1': '90',
                        'SuitTeach': 'RadioButton1',
                        'TeacherGood': '',
                        'TeacherChange': '',
                        'TeachForm': 'RadioButton4',
                        'HopeTeachForm': 'RadioButton12',
                        'TeachTool': 'RadioButton8',
                        'btnSave': '·确定·',
                    }
                data['__VIEWSTATE'] = str(__VIEWSTATE)
                data['__EVENTVALIDATION'] = str(__EVENTVALIDATION)
                post_course_data_result_html = post_course_data(s, headers, course_url, data)
                # 获取post状态
                post_course_data_result = post_course_data_result_pattern(post_course_data_result_html)
                if post_course_data_result == ["('你的评教结果已被成功保存！请关闭本窗口！')"]:
                    print('评教成功！\n')
                    finsh += 1
                else:
                    print('评教失败，请联系开发者\n')
    s.close()
    print('-' * 60)
    print('\n总共有' + str(sum) + '门课，未开课或已截止评教' + str(other) + '门课，' + '原本已评教' + str(finshed) + '门课，本次评教' + str(
        finsh) + '门课，请查收!\n')
    print('该脚本于30秒后自动退出')
    time.sleep(30)


if __name__ == "__main__":
    main()
    
