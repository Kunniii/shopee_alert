const puppeteer = require('puppeteer');
const { format } = require('date-fns');
const fs = require('fs');

async function scrapeAndScreenshot(url, filename) {
    try {
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }); // Launch headless browser
        const page = await browser.newPage();
        await page.setViewport({
            width: 1500,
            height: 920,
            deviceScaleFactor: 1,
            isMobile: false
        });

        await page.goto(url, { waitUntil: 'networkidle2' });
        await page.screenshot({ path: `${filename}.png`, fullPage: true });

        // const html = await page.evaluate(() => { return document.querySelector('.order-process-detail-list').outerHTML })
        // fs.writeFileSync(`${filename}.html`, html, { encoding: 'utf8' });

        await page.close();
        await browser.close();
    } catch (error) {
        console.error(`An error occurred: ${error}`);
    }
}


async function main() {
    // const code = "SPXVN04842113686B"
    // const url = 'https://spx.vn/track?$$CODE$$'.replace('$$CODE$$', code);

    const url = 'https://donhang.ghn.vn/?order_code=G8XYY3RH'
    const code = 'G8XYY3RH'

    const timestamp = format(new Date(), 'yyyyMMdd_HHmmss');
    const filename = `screenshot_${code}_${timestamp}`;
    await scrapeAndScreenshot(url, filename);
}

main();