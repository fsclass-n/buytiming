# PickTiming 최종 발표 패키지

**발표자: 3조 조장 박미금. PPT 3분 + 웹 시연 7분.**

## 사용할 파일

| 용도 | 파일 |
|---|---|
| 편집·발표 | [프로젝트_발표자료.pptx](../프로젝트_발표자료.pptx) |
| 검토·화면 공유 | [프로젝트_발표자료.pdf](../pdf/프로젝트_발표자료.pdf) |
| 발표 연습 | [3분 발표 대본 PDF](3분_발표대본.pdf) · [Markdown](3분_발표대본.md) |
| 웹 시연 | [7분 시연 시나리오 PDF](7분_시연시나리오.pdf) · [Markdown](7분_시연시나리오.md) |
| 변경 내용 | [수정 보고서 PDF](수정사항_보고서.pdf) · [Markdown](수정사항_보고서.md) |
| 검수 | [검수 결과](검수결과.md) · [슬라이드 미리보기](슬라이드_미리보기.png) |

PowerPoint의 발표자 보기를 켜면 슬라이드별 대본과 전환 멘트를 확인할 수 있습니다.

## 내용과 출처

- 10장(표지·소개·배경·목표·구성·기능·계정·차별성·효과·마무리). 대본 예산 170초, 브라우저 전환 여유 10초.
- 원본 13장의 문제 정의, 사용자 여정, 판정 기준, 향후 계획을 유지했습니다.
- 현재 이름 PickTiming과 원본 구성원을 유지하고, 조장·발표자는 사용자 지정 박미금으로 반영했습니다.
- 화면은 공개 Netlify의 실제 UI입니다. 상품·가격·AI 문장은 데모이며 운영 측정 결과가 아닙니다.
- 캡처 출처: `assets/capture-manifest.json`. 시연 장애 시 `assets/` 이미지를 사용할 수 있습니다.
- 구현 근거·미확인 주장 처리: [제작 기준](제작기준.md).

## 편집과 재생성

일반적인 문구·도형 편집은 PPT에서 바로 할 수 있습니다. 스크린샷 내부 요소는 이미지입니다.
아래 도구는 전체 결과물을 다시 만들 때 사용합니다.

필요 환경: Windows, Microsoft PowerPoint, 한글(HWP Automation),
Noto Sans KR, Python 3.11, Git CLI. 캡처를 새로 만들 때는 Playwright와 Edge가 필요합니다.
Python 패키지는 `python-pptx`, `PyMuPDF`, `reportlab`, `fonttools`, `lxml`, `Pillow`, `playwright`입니다.
확인한 주요 버전은 python-pptx 1.0.2, PyMuPDF 1.26.5, reportlab 4.4.4입니다.

제작 소스:

| 소스 | 역할 |
|---|---|
| `tools/story.json` | 슬라이드 제목·대본·시간·전환 멘트 |
| `tools/build_presentation.py` | 원본 PPT 기반 10장 리디자인·발표자 노트·대본 생성 |
| `tools/artifact_content.py` | 단계별 산출물·진행일지의 검증된 내용 |
| `tools/build_hwpx.py` | 원본 HWPX 표·스타일을 이용한 개정본 생성 |
| `tools/export_presentation.ps1` | 실제 PowerPoint PDF 출력·텍스트 높이 검사 |
| `tools/export_hwpx.ps1` | 실제 한글 열기·재저장·PDF 출력 |
| `tools/finalize_documents.py` | 보조 PDF·미리보기·내용/영역/링크 검수 |
| `tools/capture_screens.py` | 공개 Netlify 데모 캡처 |

원본은 Git 커밋 `279a4ce`에서 읽습니다. 얕은 복제본에는 해당 이력이 필요합니다.
빌드 명령은 Git을 사용할 수 있는 터미널에서 실행합니다. 현재 Windows에서는 Git Bash에서 확인했습니다.

```bash
# 저장소 루트, 문서용 Python 환경 활성화 후
python docs/발표자료/tools/build_presentation.py
python docs/발표자료/tools/build_hwpx.py
```

Windows PowerShell 5에서 한글 경로가 깨지지 않도록 UTF-8로 스크립트를 읽어 실행합니다.

```powershell
$docsRoot = (Resolve-Path 'docs').Path
$code = [IO.File]::ReadAllText((Join-Path $docsRoot '발표자료\tools\export_presentation.ps1'), [Text.Encoding]::UTF8)
& ([ScriptBlock]::Create($code)) $docsRoot
$code = [IO.File]::ReadAllText((Join-Path $docsRoot '발표자료\tools\export_hwpx.ps1'), [Text.Encoding]::UTF8)
& ([ScriptBlock]::Create($code)) $docsRoot
```

```bash
python docs/발표자료/tools/finalize_documents.py
```

재생성하면 PPT의 수동 편집 내용은 덮어씁니다. 지속할 변경은 소스에도 반영합니다.
대본을 바꾸면 참고 음성 시간도 다시 측정하고, 실제 발표자 리허설로 3분·7분을 확인합니다.
문서 제작 도구는 운영 DB와 배포 설정을 변경하지 않습니다.
