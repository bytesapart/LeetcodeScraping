# LeetcodeScraping
Scraping and producing PDFs for Leetcode

To get the git submodule also, do the following
```bash
git clone git@github.com:bytesapart/LeetcodeScraping.git
cd LeetcodeScraping
git submodule update --init --recursive
```

1. Runs only on Linux/MacOSX systems, as pycookiecheat borrows your session from a
chrome login and uses that in order to bypass captcha during login.
2. On Ubuntu/Debian systems, wkhtmltopdf does not come with QtWebEngine patch. Hence,
install wkhtmltopdf using the .deb located at https://github.com/wkhtmltopdf/packaging/releases/
3. If your Leetcode account is not premium, it will fetch all free questions and make
an epub/PDF of it.
4. The releases for this repo contain a Premium scrapped LeetCode questions and answers
in C++ and Python