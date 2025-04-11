const critical = require('critical')
const fs = require('fs')
const glob = require('glob')
const path = require('path')

console.log('--------------------------------')
console.log('[Generating critical css for each html file]')

console.log('Creating critical css for: index.html')
critical
  .generate({
    inline: false,
    src: 'index.html',
    width: 1300,
    height: 900,
    base: '../',
    ignore: { atrule: ['@charset'] }
  })
  .then(function (result) {
    const htmlLines = result.html.split('\n')

    if (htmlLines[389].trim() !== '/* cpcss */') {
      throw new Error(
        "index.html line 390: '/* cpcss */' for generated CSS not found. CPCSS-Build for index.html failed."
      )
    }
    htmlLines[389] = result.css
    let htmlWithCriticalCSS = htmlLines.join('\n')

    fs.writeFileSync('../index.html', htmlWithCriticalCSS)
  })
  .then(function () {
    glob('../journal/**/*.html', function (err, files) {
      if (err) throw err

      for (const filepath of files) {
        console.log('Creating critical css for: ' + path.basename(filepath))
        const filename = path.basename(filepath).split('.')[0]

        critical.generate({
          inline: false,
          base: '../',
          src: filepath,
          width: 1300,
          height: 900,
          target: './stylesheets/inline/critical/' + filename + '.css',
          ignore: { atrule: ['@charset'] }
        })
      }
    })
  })
  .catch(function (err) {
    console.error(err)
    process.exitCode = 1
  })
