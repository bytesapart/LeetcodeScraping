from typing import List

import urls
from session import LeetCodeSession
from models import Problem, ProblemDetail
from pycookiecheat import chrome_cookies
import requests


class LeetCodeClient(LeetCodeSession):
    def get_problems(self) -> List[Problem]:
        cookies = chrome_cookies(urls.LOGIN)
        self.s.cookies = requests.utils.cookiejar_from_dict(cookies)
        r = self.s.get(urls.PROBLEMS)
        try:
            a = r.json()["stat_status_pairs"]
            return [Problem(d) for d in a]
        except:
            return []

    def get_problem_detail(self, question_slug: str) -> ProblemDetail:
        cookies = chrome_cookies(urls.LOGIN)
        self.s.cookies = requests.utils.cookiejar_from_dict(cookies)
        csrf = self.s.cookies.get("csrftoken")
        body = '{"operationName":"questionData","variables":{"titleSlug":"%s"},"query":"query questionData($titleSlug: String!) {\\n  question(titleSlug: $titleSlug) {\\n    questionId\\n    questionFrontendId\\n    boundTopicId\\n    title\\n    titleSlug\\n    content\\n    translatedTitle\\n    translatedContent\\n    isPaidOnly\\n    difficulty\\n    likes\\n    dislikes\\n    isLiked\\n    similarQuestions\\n    contributors {\\n      username\\n      profileUrl\\n      avatarUrl\\n      __typename\\n    }\\n    langToValidPlayground\\n    topicTags {\\n      name\\n      slug\\n      translatedName\\n      __typename\\n    }\\n    companyTagStats\\n    codeSnippets {\\n      lang\\n      langSlug\\n      code\\n      __typename\\n    }\\n    stats\\n    hints\\n    solution {\\n      id\\n      canSeeDetail\\n      __typename\\n    }\\n    status\\n    sampleTestCase\\n    metaData\\n    judgerAvailable\\n    judgeType\\n    mysqlSchemas\\n    enableRunCode\\n    enableTestMode\\n    envInfo\\n    __typename\\n  }\\n}\\n"}' % question_slug
        r = self.s.post(urls.GRAPHQL,
                        data=body,
                        headers={"referer": urls.DESCRIPTION % question_slug,
                                 "X-CSRFToken": csrf,
                                 "Content-Type": "application/json"})
        d = {}
        try:
            d = r.json()["data"]["question"]
        except:
            pass
        return ProblemDetail(d or {})
