# prototype-rss-news.py / trgr_post.py / trgr_post_with_ai.py
A prototype for news acquisition methods combining RSS and LLM

<br>

## What is this
Redesigned a personal RSS news link collection distribution program as an international version.
- [trgr_post.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/trgr_post.py): Symbolic translation system (basic version)
- [trgr_post_with_ai.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/trgr_post_with_ai.py): Gemini 2.0 Flash batch translation (API efficiency version)
- [prototype-rss-news.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g/prototype-rss-news.py): **RSS + Gemma 3 1B** international version proof of concept. [Sample is available here](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/tree/main/g).
- [prototype-rss-news-v2.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g-v2/prototype-rss-news-v2.py): **RSS + Qwen2.5VL 7B** Classification with Reasoning. [Sample is available here](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/tree/main/g-v2).


<br>

## How to use
I think it would be comfortable to have Gmail app passwords and Gemini API keys.

From the perspective of democratizing technology, prototype-rss-news.py actually runs the program on a 2018 PC as a home server in a CUI/CLI environment. 4GB memory is tough for running open-source AI.

However,
```
8th Gen Intel Core i3-8100 (Coffee Lake)
4 cores
16GB memory
500GB HDD storage
```
With the above environment, there are open-source options. Even with old computers, there are things that can be done.

<br>

### Addendum – 2025/07/17:
I also wrote a program that uses [Qwen2.5VL 7B to generate classifications and their reasoning](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g-v2/prototype-rss-news-v2.py). It runs in the environment shown below. For the model, I chose one different from the ones used in browser- or app-based services like ChatGPT or Gemini 2.5 Pro, as this is in preparation for news analysis. You can change the model to any one you like from the official site: https://ollama.com/.

<br>

```
CPU: AMD Ryzen 5 6600H
Cores: 12
Memory: 32 GB
GPU: Radeon 680M (integrated)
1TB HDD storage
```


<br>

### Addendum 2 – 2025/07/17

In [prototype-rss-news-v2.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g-v2/prototype-rss-news-v2.py), an issue was found where outdated information was being retrieved from official RSS feeds.

Filtering was implemented in [prototype-rss-news-v3.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g-v3/prototype-rss-news-v3.py), but it was incomplete.

Therefore, a new script, [prototype-rss-news-v4.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/g-4v/prototype-rss-news-v4.py), was created focusing solely on RSS retrieval.

<br>

## **Project Philosophy**
Technology should serve human dignity, not replace it.

If you are in a developing country, you can utilize this for improving education and social structural issues. If you are in a developed country, in addition to that, I expect you can deal with information flooding and information overload. Wherever in the world you are, information is important for holding hope and drawing dreams.

<br>

## Related Repositories
Information overload countermeasures:
https://github.com/trgr-karasutoragara/zen-info-your-life-is-yours

Democratization of learning and reading:
https://github.com/trgr-karasutoragara/AI-empowers-your-mind-to-reach-anywhere

Philosophical foundation "future AI x dignity":
https://github.com/trgr-karasutoragara/trgr-karasutoragara.github.io

<br>

---

# Simple Your Private Memo
A local tool designed for mouse-centric browsing and information literacy education for elderly users. Implemented as a single Python file with no external server communication, including cloud services.

[Read more →](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/README.md)

<br>

---

<br>

## License
MIT License

<br>

## Author Declaration
I am an unaffiliated volunteer individual, and there is no conflict of interest in this project.
