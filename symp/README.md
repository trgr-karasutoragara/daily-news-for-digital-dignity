# Simple Your Private Memo

A local tool designed for mouse-centric browsing and information literacy education for elderly users. Implemented as a single Python file with no external server communication, including cloud services.

<br>

## Demo

### Demo: Using jp-sypm.py on Ubuntu (Memo and Simple Prompt Generation)

https://youtu.be/JVEb8CWXVy4

### Demo: Using en-sypm.py on Ubuntu (Memo and Simple Prompt Generation)

https://youtu.be/uxX-iD2nKLk

<br>

## Screenshots

| **Launched on Chromebook** | **Selected text and saved it to a memo on the localhost** |
| :---: | :---: |
| <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-01.42.20.png" width="400"> | <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-01.42.46.png" width="400"> |
| **Examples of saving and prompts** | **Selected text and saved it to a memo on the localhost** |
| <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-01.43.14.png" width="400"> | <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-02.03.10.png" width="400"> |
| **Examples of saving and prompts** |  |
| <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-02.03.33.png" width="400"> | |
| **Prompt usage examples with Gemini 2.5 Pro** | **Prompt usage examples with Gemini 2.5 Pro** |
| <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-02.03.55.png" width="400"> | <img src="https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/img/Screenshot-2025-07-16-02.04.28.png" width="400"> |

<br>

## Elderly Welfare and Information Literacy Education

Tested and confirmed working on Chromebook and Ubuntu (as of July 16, 2025). This tool enables simple AI prompt generation and local memo management through mouse clicks.

1. **Mouse-friendly design**: Elderly users who prefer voice operation over keyboard input can still utilize this tool effectively through mouse operations
2. **Reduced AI verification burden**: Multiple prompt generation reduces the effort required for AI confirmation, making verification more accessible
3. **Welfare and educational proposal**: This program serves as a prototype proposal for welfare and educational applications
4. **Data sovereignty focus**: Uses bookmarklet and Python combination for localhost stability and data sovereignty, avoiding Chrome extensions

<br>

## Quick Start

**English version:** [en-sypm.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/en-sypm.py)

**Japanese version:** [jp-sypm.py](https://github.com/trgr-karasutoragara/daily-news-for-digital-dignity/blob/main/symp/jp-sypm.py)

<br>

1. **Chromebook**: Enable Linux development environment
2. **Ubuntu/Chromebook**: Run `en-sypm.py` or `jp-sypm.py` from terminal in any folder
3. **Browser access**: English version at `localhost:8001`, Japanese version at `localhost:8000`
4. **Setup bookmarklet**: Add the bookmarklet to your bookmark bar
5. **Usage**: Select text and click the bookmarklet
6. **Fallback method**: For non-functional sites, copy text and manually add to localhost page for automatic prompt generation

<br>

## Important Notes

**Local tool design**: This tool allows CORS (Access-Control-Allow-Origin: *) and is designed as a "personal local tool."

**Port configuration**: As mentioned above. Save files are created in the same directory as the Python file.

**⚠️ Not recommended for external server deployment**

<br>

## FAQ

**Q: Why make it public?**

**A: Because it's a contribution to humanity.**

As I published in "[Future AI x Dignity: A practical framework for implementing ethics in elderly tech support through AI integration](https://github.com/trgr-karasutoragara/trgr-karasutoragara.github.io)," I am working on ensuring that my mother can age with peace of mind, and that her freedom and dignity are protected.

Is it enough for only my own family's freedom and dignity to be protected? Even if it's just a prototype, when I design tools, by making them public under the MIT License, they might be useful to others in the fields of elderly welfare and information literacy.

Welfare, education, aging, dignity, freedom. Aren't all of these indispensable to humanity?

<br>

**Q: How do you consider copyright issues?**  
A: This is a tool for welfare and educational purposes. In the demo, I used public domain materials and my own work as examples. To ensure continued research and development of such tools, please use this ethically and avoid misuse.

<br>

**Q: Are there usage guidelines?**  
A: The intended scope is equivalent to what an individual would write in a paper notebook or request from AI personally.

<br>

## License

MIT License

<br>

## Author Declaration

I am an unaffiliated volunteer individual, and there is no conflict of interest in this project.
