import { Telegraf } from 'telegraf';
import sqlite3 from 'sqlite3';
const puppeteer = require('puppeteer');
const { format } = require('date-fns');
const fs = require('fs');
const path = require('path'); // Import the 'path' module


async function scrapeAndScreenshot(url, filename) {
    try {
        const browser = await puppeteer.launch({
            headless: 'new', // Use 'new' for a clean headless environment
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();
        await page.setViewport({ width: 1500, height: 920 });
        await page.goto(url, { waitUntil: 'networkidle2' });

        // Check if the screenshot directory exists, create it if not
        const screenshotDir = path.dirname(filename);
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }

        await page.screenshot({ path: filename, fullPage: true });
        await page.close();
        await browser.close();
        return filename; // Return the filename
    } catch (error) {
        console.error(`An error occurred during screenshot: ${error}`);
        return null; // Return null on error
    }
}


const BOT_TOKEN = process.env.BOT_TOKEN;

const bot = new Telegraf(BOT_TOKEN);

const db = new sqlite3.Database('./database.sqlite');

// Start command
bot.start((ctx) => ctx.reply('Welcome to the shipment tracking bot!'));

// Help command
bot.help((ctx) => ctx.reply(
    'Available commands:\n' +
    '/start - Start the bot.\n' +
    '/help - Show this help message.\n' +
    '/add_ship `code` `provider` - Add a new shipment (code and provider are required).\n' +
    '/status `code` - Get the tracking URL for a shipment by its code.\n' +
    '/update `code` `status` - Update the status of a shipment (status: delivered or not_delivered).\n' +
    '/providers - List all available shipping providers.\n' +
    '/add_provider `name` `url` - Add a new shipping provider (name and url are required).\n' +
    '/ongoing_shipments - List all ongoing shipments.'
));

// Add shipment command
bot.command('add_ship', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length < 2) {
        ctx.reply('Usage: /add_shipment <code> <provider>');
        return;
    }
    const code = args[0];
    const provider = args[1].toUpperCase();

    db.get('SELECT COUNT(*) AS count FROM shipments WHERE CODE = ?', [code], (err, row) => {
        if (err) {
            ctx.reply(`Error checking shipment: ${err.message}`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }
        if (row.count > 0) {
            ctx.reply(`Shipment with code \`${code}\` already exists.`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }

        db.run(`INSERT INTO shipments (CODE, PROVIDER_ID, STATUS) VALUES (?, (SELECT ID FROM ship_providers WHERE NAME = ?), 0)`, [code, provider], (err) => {
            if (err) {
                ctx.reply(`Error adding shipment: ${err.message}`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            } else {
                ctx.reply(`Shipment added with code: \n\`\`\`\n${code}\n\`\`\``, { parse_mode: 'Markdown', disable_web_page_preview: true });
            }
        });
    });
});

// Update shipment status command
bot.command('update', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length < 2) {
        ctx.reply('Usage: /update `code` `[true|false]`', { parse_mode: 'Markdown' });
        return;
    }
    const code = args[0];
    const status = args[1].toLowerCase();

    if (status !== 'true' && status !== 'false') {
        ctx.reply('Invalid status. Use "true" or "false"', { parse_mode: 'Markdown' });
        return;
    }

    const newStatus = status === 'true' ? 1 : 0;

    db.run(`UPDATE shipments SET STATUS = ? WHERE CODE = ?`, [newStatus, code], function (err) {
        if (err) {
            ctx.reply(`Error updating status: ${err.message}`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }
        ctx.reply(`Shipment status updated to \`${status}\`.`, { parse_mode: 'Markdown', disable_web_page_preview: true });
    });
});

// shipment status
bot.command('status', async (ctx) => {
    const code = ctx.message.text.split(' ')[1];
    if (!code) {
        ctx.reply('Usage: /status `code`', { parse_mode: 'Markdown', disable_web_page_preview: true });
        return;
    }

    db.get(`SELECT sp.URL, s.STATUS FROM shipments s JOIN ship_providers sp ON s.PROVIDER_ID = sp.ID WHERE s.CODE = ?`, [code], async (err, row) => {
        if (err) {
            ctx.reply(`Error getting shipment details: ${err.message}`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }
        if (!row) {
            ctx.reply(`Shipment with code '${code}' not found.`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }

        const url = row.URL.replace('$$CODE$$', code);
        console.log(url);
        
        const status = row.STATUS ? 'Delivered' : 'Not Delivered';

        ctx.reply(`Shipment Status: \`${status}\``, { parse_mode: 'Markdown', disable_web_page_preview: true }); // Status message
        ctx.reply(`You can also check at this url\n${url}`, { disable_web_page_preview: true })
        const timestamp = format(new Date(), 'yyyyMMdd_HHmmss');
        const filename = `screenshots/${code}_${timestamp}.png`;

        ctx.reply('Fetching shipment details...', { disable_web_page_preview: true });
        const screenshotPath = await scrapeAndScreenshot(url, filename);

        if (screenshotPath) {
            try {
                await ctx.replyWithPhoto({ source: fs.createReadStream(screenshotPath) });
                fs.unlinkSync(screenshotPath);
            } catch (error) {
                ctx.reply(`Error sending photo: ${error.message}`, { parse_mode: 'Markdown', disable_web_page_preview: true });
            }
        } else {
            ctx.reply(`Error capturing screenshot.`, { parse_mode: 'Markdown', disable_web_page_preview: true });
        }
    });
});

// List providers command
bot.command('providers', (ctx) => {
    db.all('SELECT * FROM ship_providers', (err, rows) => {
        if (err) {
            ctx.reply(`Error listing providers: ${err.message}`);
        } else {
            const providerList = rows.map(row => `${row.NAME} (${row.URL})`).join('\n');
            ctx.reply(`Available providers:\n${providerList}`, { disable_web_page_preview: true });
        }
    });
});

// Add provider command
bot.command('add_provider', (ctx) => {
    const args = ctx.message.text.split(' ').slice(1);
    if (args.length < 2) {
        ctx.reply('Usage: /add_provider `name` `url`');
        return;
    }
    const name = args[0];
    const url = args[1];
    db.run(`INSERT INTO ship_providers (NAME, URL) VALUES (?, ?)`, [name, url], (err) => {
        if (err) {
            ctx.reply(`Error adding provider: ${err.message}`);
        } else {
            ctx.reply(`Provider '${name}' added successfully.`);
        }
    });
});

bot.command('ongoing_shipments', (ctx) => {
    db.all(`SELECT s.ID, s.CODE, sp.NAME, s.STATUS 
            FROM shipments s 
            JOIN ship_providers sp ON s.PROVIDER_ID = sp.ID 
            WHERE s.STATUS = 0`, (err, rows) => {
        if (err) {
            ctx.reply(`Error retrieving ongoing shipments: \`${err.message}\``, { parse_mode: 'Markdown', disable_web_page_preview: true });
            return;
        }
        if (rows.length === 0) {
            ctx.reply('No ongoing shipments found.');
            return;
        }

        let res = 'Ongoing shipment:\n'

        for(let row of rows) {
            res += `**${row.NAME.toUpperCase()}**  \n\`\`\`\n${row.CODE}\n\`\`\`\n`
        }

        ctx.reply(res, { parse_mode: 'Markdown', disable_web_page_preview: true });
    });
});


bot.launch();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));