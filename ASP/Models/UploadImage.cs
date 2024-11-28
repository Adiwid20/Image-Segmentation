using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Http;

namespace UjiCoba.Models
{
    public class UploadImage
    {
        [Required(ErrorMessage = "File gambar harus dipilih.")]
        public IFormFile ImageFile { get; set; }
    }
}