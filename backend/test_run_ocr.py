from pathlib import Path
import ocr_service

img = Path('screenshots/1f78ed07-0fc1-4e7e-84e7-e9def81be264_p1.png')
print('image exists', img.exists())
res = ocr_service.run_ocr(None, img, page_number=1)
print('num entries', len(res))
all_text = ' '.join(e['text'] for e in res)
print('total text length', len(all_text))
print('preview', all_text[:200])
