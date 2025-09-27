# PyHTML
PyHTML is a markup language inspired by Python that compiles to HTML.

## Sample (sample.pyhtml)
```
div class="window" style="position: absolute; left: 10px; top 10px;":
    << "textline"
    div class="title":
        << "another textline"
    << "multi
line
text"
```

### Result (sample.html)
```html
<div class='window' style='position: absolute; left: 10px; top 10px;'>
textline
    <div class='title'>
another textline
    </div>
multi
line
text
</div>
```

## Usage
```
python3 pyhtml.py debian_trixie_postfix_dovecot_howto.pyhtml
```
