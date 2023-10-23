const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
const RecaptchaPlugin = require("puppeteer-extra-plugin-recaptcha");
const commander = require("commander");
const fs = require("fs");
const { IncomingWebhook } = require("@slack/webhook");
const chalk = require("chalk");
const sleep = require("sleep-promise");
const path = require("path");
require("log-timestamp");

commander
    .name("domsprayer")
    .description(
        "A generic DOM-based password sprayer"
    )
    .version("2.0.0")
    .option("-t, --target <url>", "Target URL")
    .option("-uf, --username-field <selector>", "Username field selector")
    .option("-pf, --password-field <selector>", "Password field selector")
    .option("-lf, --login-button <selector>", "Login button selector")
    .option("-u, --usernames <file>", "Path to the usernames file")
    .option("-p, --passwords <file>", "Path to the passwords file")
    .option(
        "-w, --wait-time <ms>",
        "Minimum time to wait for page to load in milliseconds",
        1000,
        parseInt
    )
    .option(
        "-i, --interval <ms>",
        "Interval between login attempts in milliseconds",
        0,
        parseInt
    )
    .option("-H, --headless", "Run in headless mode", false)
    .option("-k, --api-key <key>", "2Captcha API key")
    .option("-s, --slack-webhook <url>", "Slack webhook URL")
    .option(
        "-o, --output <outputFile>",
        "Specify the output file name",
        "valid_creds.txt"
    )
    .option(
        "--test",
        "Test bot detection and take screenshot of the results",
        false
    )
    .option(
        "--demo",
        "Run in demo mode (do not output passwords to the screen)",
        false
    )
    .option(
        "--typing-delay <ms>",
        "Delay for typing in milliseconds",
        100,
        parseInt
    )
    .option(
        "-S, --screenshot",
        "Take screenshot on successful login or on unexpected behaviour",
        false
    )
    .option(
        "-d, --directory <dir>",
        "Directory to save screenshots when using -S",
        "screenshots"
    )
    .parse();

const options = commander.opts();

// Validate options
if (!options.test && (!options.usernames || !options.passwords)) {
    console.error(chalk.red("Usernames file and passwords file are required!"));
    process.exit(1);
}
// Remove trailing slashes from path
options.directory = path.normalize(options.directory);

// Check if directory exists and create it if it doesn't
if (!fs.existsSync(options.directory)) {
    fs.mkdirSync(options.directory);
    console.log(
        chalk.cyan("Directory", chalk.underline(options.directory), "created.")
    );
}

let client2captcha = null;

// Initialize 2Captcha client if API key was provided
if (options.apiKey) {
    client2captcha = new Client(options.apiKey, {
        timeout: 60000,
        polling: 5000,
        throwErrors: false,
    });
}
