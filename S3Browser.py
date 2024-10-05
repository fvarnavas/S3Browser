import boto3
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse

# Initialize the S3 client
s3_client = boto3.client('s3')


class S3BrowserHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        if len(path_parts) == 1 and path_parts[0] == '':
            self.list_buckets()
        elif len(path_parts) == 2 and path_parts[0] == 'bucket':
            self.list_files(path_parts[1])
        elif len(path_parts) == 3 and path_parts[0] == 'download':
            self.download_file(path_parts[1], path_parts[2])
        else:
            self.send_error(404, "File not found")

    def list_buckets(self):
        buckets = s3_client.list_buckets()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><head><title>S3 Buckets</title></head><body>")
        self.wfile.write(b"<h1>S3 Buckets</h1><ul>")
        for bucket in buckets['Buckets']:
            self.wfile.write(f"<li><a href='/bucket/{bucket['Name']}'>{bucket['Name']}</a></li>".encode())
        self.wfile.write(b"</ul></body></html>")

    def list_files(self, bucket_name):
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><head><title>Files</title></head><body>")
        self.wfile.write(f"<h1>Files in {bucket_name}</h1><ul>".encode())
        for obj in objects.get('Contents', []):
            self.wfile.write(f"<li><a href='/download/{bucket_name}/{obj['Key']}'>{obj['Key']}</a></li>".encode())
        self.wfile.write(b"</ul></body></html>")

    def download_file(self, bucket_name, file_name):
        file_path = os.path.join('/tmp', file_name)
        s3_client.download_file(bucket_name, file_name, file_path)
        self.send_response(200)
        self.send_header('Content-Disposition', f'attachment; filename="{file_name}"')
        self.send_header('Content-type', 'application/octet-stream')
        self.end_headers()
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())


if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, S3BrowserHandler)
    print("Starting server on port 8000...")
    httpd.serve_forever()