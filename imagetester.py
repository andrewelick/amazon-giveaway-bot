def captcha_tester():
    try:
        from PIL import Image
    except ImportError:
        import Image
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract'

    return pytesseract.image_to_string(Image.open('captcha.png'))
